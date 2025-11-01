import logging
import math
import os
from functools import lru_cache
from types import SimpleNamespace
from typing import Any, Optional, Sequence, Tuple, Union

import requests
import hashlib
from concurrent.futures import ThreadPoolExecutor
import time
import re

from urllib.parse import quote
from huggingface_hub import snapshot_download

try:  # pragma: no cover - optional dependency
    from qdrant_client import QdrantClient as ExternalQdrantClient
except ImportError:  # pragma: no cover - optional dependency
    ExternalQdrantClient = None

try:  # pragma: no cover - optional dependency
    from qdrant_client.http import models as qdrant_models
except ImportError:  # pragma: no cover - optional dependency
    qdrant_models = None

from langchain.retrievers import ContextualCompressionRetriever, EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.retrievers import BaseRetriever

from open_webui.config import (
    LEGAL_RAG_BASE_FIELDS,
    LEGAL_RAG_COLLECTION,
    LEGAL_RAG_DEFAULT_FEATURE_KEYS,
    LEGAL_RAG_MAX_RESULTS,
    QDRANT_API_KEY,
    QDRANT_TIMEOUT,
    QDRANT_URI,
    RAG_EMBEDDING_CONTENT_PREFIX,
    RAG_EMBEDDING_PREFIX_FIELD_NAME,
    RAG_EMBEDDING_QUERY_PREFIX,
    VECTOR_DB,
)
from open_webui.retrieval.vector.factory import VECTOR_DB_CLIENT


from open_webui.models.users import UserModel
from open_webui.models.files import Files
from open_webui.models.knowledge import Knowledges

from open_webui.models.chats import Chats
from open_webui.models.notes import Notes

from open_webui.retrieval.vector.main import GetResult
from open_webui.utils.access_control import has_access
from open_webui.utils.misc import get_message_list

from open_webui.retrieval.web.utils import get_web_loader
from open_webui.retrieval.loaders.youtube import YoutubeLoader


from open_webui.env import (
    SRC_LOG_LEVELS,
    OFFLINE_MODE,
    ENABLE_FORWARD_USER_INFO_HEADERS,
)

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["RAG"])


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip().lower()


def _invoke_embedding(embedding_function, text, prefix=None, user=None):
    if embedding_function is None:
        return None
    return embedding_function(text, prefix, user)


def _convert_embedding(value) -> list[float]:
    if value is None:
        return []
    if isinstance(value, list):
        try:
            return [float(v) for v in value]
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return []
    if hasattr(value, "tolist"):
        try:
            return [float(v) for v in value.tolist()]
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return []
    try:
        return [float(v) for v in value]
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return []


def _convert_embeddings(value) -> list[list[float]]:
    embeddings: list[list[float]] = []
    if value is None:
        return embeddings
    if isinstance(value, list):
        for item in value:
            converted = _convert_embedding(item)
            if converted:
                embeddings.append(converted)
    else:
        converted = _convert_embedding(value)
        if converted:
            embeddings.append(converted)
    return embeddings


def _normalize_vector(vector: Sequence[float]) -> list[float]:
    if not vector:
        return []
    norm = math.sqrt(sum(v * v for v in vector))
    if not norm:
        return [float(v) for v in vector]
    return [float(v) / norm for v in vector]


def _align_vector_dimensions(vector: Sequence[float], expected_size: Optional[int]) -> list[float]:
    if not vector or not expected_size or expected_size <= 0:
        return [float(v) for v in vector] if vector else []
    current_size = len(vector)
    if current_size == expected_size:
        return [float(v) for v in vector]
    if current_size > expected_size:
        return [float(v) for v in vector[:expected_size]]
    padded = list(vector) + [0.0] * (expected_size - current_size)
    return [float(v) for v in padded]


def _average_vectors(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    length = len(vectors[0])
    totals = [0.0] * length
    count = 0
    for vector in vectors:
        if len(vector) != length:
            continue
        totals = [a + b for a, b in zip(totals, vector)]
        count += 1
    if not count:
        return []
    return [value / count for value in totals]


def _cosine_scores(vectors: list[list[float]], reference: list[float]) -> list[float]:
    if not vectors or not reference:
        return []
    reference_vector = _normalize_vector(reference)
    scores: list[float] = []
    for vector in vectors:
        normalized = _normalize_vector(vector)
        if not normalized or len(normalized) != len(reference_vector):
            scores.append(0.0)
            continue
        scores.append(sum(a * b for a, b in zip(normalized, reference_vector)))
    return scores


def _extract_vector_from_scored_point(point) -> list[float]:
    if point is None:
        return []
    vector = getattr(point, "vector", None)
    if vector is None and getattr(point, "payload", None):
        vector = point.payload.get("vector")
    if isinstance(vector, dict):
        for value in vector.values():
            converted = _convert_embedding(value)
            if converted:
                return converted
        return []
    return _convert_embedding(vector)


def _normalize_scored_point(point, default_score: float = 0.0):
    if point is None:
        return None
    if isinstance(point, SimpleNamespace):
        return point
    payload = getattr(point, "payload", None)
    vector = getattr(point, "vector", None)
    score = getattr(point, "score", default_score)
    identifier = getattr(point, "id", None)
    if payload is None and isinstance(point, dict):
        payload = point.get("payload")
        vector = point.get("vector")
        score = point.get("score", default_score)
        identifier = point.get("id")
    if payload is None:
        payload = {}
    return SimpleNamespace(id=identifier, payload=payload, vector=vector, score=score)


@lru_cache(maxsize=1)
def _get_legal_qdrant_client():
    if not LEGAL_RAG_COLLECTION:
        return None
    if ExternalQdrantClient is None:
        return None
    if not QDRANT_URI:
        return None
    try:
        return ExternalQdrantClient(
            url=QDRANT_URI,
            api_key=QDRANT_API_KEY or None,
            timeout=QDRANT_TIMEOUT,
        )
    except Exception as exc:  # pragma: no cover - network dependent
        log.debug(f"Unable to initialize legal Qdrant client: {exc}")
        return None


_LEGAL_VECTOR_DIM_MISMATCH_REPORTED = False


@lru_cache(maxsize=1)
def _legal_collection_vector_size() -> Optional[int]:
    client = _get_legal_qdrant_client()
    if not client or not LEGAL_RAG_COLLECTION:
        return None
    try:
        info = client.get_collection(LEGAL_RAG_COLLECTION)
    except Exception as exc:  # pragma: no cover - network dependent
        log.debug(f"Unable to fetch legal collection info: {exc}")
        return None

    config = getattr(info, "config", None)
    params = getattr(config, "params", None) if config else None
    vectors = getattr(params, "vectors", None) if params else None
    size = getattr(vectors, "size", None) if vectors else None
    if isinstance(size, int) and size > 0:
        return size
    return None


@lru_cache(maxsize=1)
def _legal_feature_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    keys = list(LEGAL_RAG_DEFAULT_FEATURE_KEYS)
    client = _get_legal_qdrant_client()
    if client:
        try:
            points, _ = client.scroll(
                LEGAL_RAG_COLLECTION,
                limit=1,
                with_payload=True,
            )
            for raw_point in points or []:
                payload = getattr(raw_point, "payload", {}) or {}
                for key in payload.keys():
                    if key in LEGAL_RAG_BASE_FIELDS:
                        continue
                    if key not in keys:
                        keys.append(key)
        except Exception as exc:  # pragma: no cover - network dependent
            log.debug(f"Unable to introspect legal features: {exc}")

    for key in keys:
        normalized = _normalize_text(key)
        if not normalized:
            continue
        aliases.setdefault(normalized, key)
        alias_with_spaces = _normalize_text(key.replace("_", " "))
        if alias_with_spaces:
            aliases.setdefault(alias_with_spaces, key)
        aliases.setdefault(_normalize_text(key.upper()), key)
    return aliases


def _detect_legal_features(queries: list[str]) -> set[str]:
    aliases = _legal_feature_aliases()
    detected: set[str] = set()
    for query in queries or []:
        normalized_query = _normalize_text(query)
        if not normalized_query:
            continue
        for alias, key in aliases.items():
            if alias and alias in normalized_query:
                detected.add(key)
    return detected


def _embed_texts(embedding_function, texts: list[str], user=None) -> list[list[float]]:
    if not texts:
        return []
    embeddings = _invoke_embedding(
        embedding_function,
        texts,
        prefix=RAG_EMBEDDING_CONTENT_PREFIX,
        user=user,
    )
    return _convert_embeddings(embeddings)


def _legal_feature_contexts(
    queries: list[str],
    embedding_function,
    user,
    max_results: int,
) -> Tuple[list[dict], list[float]]:
    client = _get_legal_qdrant_client()
    if not client or not queries or embedding_function is None:
        return [], []

    expected_vector_size = _legal_collection_vector_size()

    alias_map = _legal_feature_aliases()
    requested_features = _detect_legal_features(queries)
    canonical_requested_features = list(
        dict.fromkeys(
            alias_map.get(_normalize_text(feature), feature)
            for feature in requested_features
        )
    )
    search_texts: list[str] = []
    seen_texts: set[str] = set()

    for query in queries:
        if not query:
            continue
        normalized_query = query.strip()
        if not normalized_query:
            continue
        if normalized_query not in seen_texts:
            search_texts.append(normalized_query)
            seen_texts.add(normalized_query)
        for feature in canonical_requested_features:
            if not feature:
                continue
            feature_phrase = feature.replace("_", " ")
            if feature_phrase.lower() in normalized_query.lower():
                continue
            combined_query = f"{normalized_query} {feature_phrase}".strip()
            if combined_query and combined_query not in seen_texts:
                search_texts.append(combined_query)
                seen_texts.add(combined_query)

    for feature in canonical_requested_features:
        if not feature:
            continue
        feature_phrase = feature.replace("_", " ")
        if feature_phrase and feature_phrase not in seen_texts:
            search_texts.append(feature_phrase)
            seen_texts.add(feature_phrase)

    if not search_texts:
        search_texts = [query for query in queries if query]

    query_vectors: list[list[float]] = []
    for query in search_texts:
        try:
            vector = _invoke_embedding(
                embedding_function,
                query,
                prefix=RAG_EMBEDDING_QUERY_PREFIX,
                user=user,
            )
            vector = _convert_embedding(vector)
            if expected_vector_size:
                if len(vector) != expected_vector_size:
                    global _LEGAL_VECTOR_DIM_MISMATCH_REPORTED
                    if not _LEGAL_VECTOR_DIM_MISMATCH_REPORTED:
                        log.error(
                            "Legal RAG embedding dimension mismatch: got %s, expected %s for collection '%s'. Applying automatic vector alignment.",
                            len(vector),
                            expected_vector_size,
                            LEGAL_RAG_COLLECTION,
                        )
                        _LEGAL_VECTOR_DIM_MISMATCH_REPORTED = True
                    vector = _align_vector_dimensions(vector, expected_vector_size)
                if len(vector) != expected_vector_size:
                    continue
            if vector:
                query_vectors.append(_normalize_vector(vector))
        except Exception as exc:  # pragma: no cover - embedding dependent
            log.debug(f"Failed to encode legal feature query '{query}': {exc}")

    def _collect_from_scroll(
        limit: int,
    ) -> tuple[list[Any], bool]:
        points: list[Any] = []
        next_offset = None
        while len(points) < limit:
            kwargs = {
                "collection_name": LEGAL_RAG_COLLECTION,
                "with_payload": True,
                "with_vectors": False,
                "limit": min(256, limit - len(points)),
            }
            if next_offset is not None:
                kwargs["offset"] = next_offset
            try:
                result = client.scroll(**kwargs)
            except Exception as exc:  # pragma: no cover - backend dependent
                log.debug(f"Legal feature scroll failed: {exc}")
                break

            if isinstance(result, tuple):
                batch, next_offset = result
            else:  # pragma: no cover - fallback for legacy client
                batch, next_offset = result, None

            if not batch:
                break

            for point in batch:
                normalized_point = _normalize_scored_point(point, default_score=1.0)
                if not normalized_point:
                    continue
                points.append(normalized_point)
                if len(points) >= limit:
                    break

            if not next_offset:
                break
        return points, True

    collected_points: list[Any] = []
    search_limit = max_results
    if query_vectors:
        for vector in query_vectors:
            try:
                result = client.search(
                    collection_name=LEGAL_RAG_COLLECTION,
                    query_vector=vector,
                    limit=search_limit,
                    with_payload=True,
                    with_vectors=True,
                )
                for point in result or []:
                    normalized_point = _normalize_scored_point(point)
                    if normalized_point:
                        collected_points.append(normalized_point)
            except Exception as exc:  # pragma: no cover - backend dependent
                log.debug(f"Legal feature vector search failed: {exc}")

    if len(collected_points) < search_limit:
        scroll_points, _ = _collect_from_scroll(
            limit=search_limit - len(collected_points),
        )
        collected_points.extend(scroll_points)

    if not collected_points:
        return [], []
    collected_points.sort(key=lambda sp: sp.score or 0.0, reverse=True)

    contexts: list[dict] = []
    vectors: list[list[float]] = []
    seen_ids: set[str] = set()

    for point in collected_points:
        point_id = str(point.id)
        if point_id in seen_ids:
            continue
        seen_ids.add(point_id)

        payload = point.payload or {}
        score = float(point.score) if point.score is not None else 0.0
        raw_vector = _extract_vector_from_scored_point(point)
        if expected_vector_size and raw_vector:
            raw_vector = _align_vector_dimensions(raw_vector, expected_vector_size)
        extracted_vector = _normalize_vector(raw_vector)

        nomor_putusan = payload.get("nomor_putusan")
        file_name = payload.get("file_name")
        document_id = payload.get("document_id")

        payload_key_map = {
            _normalize_text(key): key
            for key in (payload.keys() if payload else [])
            if isinstance(key, str)
        }

        def _canonicalize_feature(raw: str) -> str:
            normalized = _normalize_text(raw)
            return alias_map.get(normalized, raw)

        extracted_items: list[tuple[str, str]] = []
        seen_features_for_point: set[str] = set()

        if canonical_requested_features:
            for feature in canonical_requested_features:
                normalized_feature = _normalize_text(feature)
                payload_key = payload_key_map.get(normalized_feature)
                if not payload_key and " " in feature:
                    payload_key = payload_key_map.get(
                        _normalize_text(feature.replace(" ", "_"))
                    )
                if not payload_key and "_" in feature:
                    payload_key = payload_key_map.get(
                        _normalize_text(feature.replace("_", " "))
                    )
                if not payload_key:
                    continue
                value = payload.get(payload_key)
                if not value:
                    continue
                content = str(value).strip()
                if not content:
                    continue
                canonical_feature = _canonicalize_feature(feature)
                if canonical_feature in seen_features_for_point:
                    continue
                seen_features_for_point.add(canonical_feature)
                extracted_items.append((canonical_feature, content))

        if not extracted_items:
            fallback_value = (payload.get("column_value") or "").strip()
            if fallback_value:
                raw_feature = payload.get("source_column") or ""
                canonical_feature = _canonicalize_feature(raw_feature or "legal")
                if canonical_feature not in seen_features_for_point:
                    seen_features_for_point.add(canonical_feature)
                    extracted_items.append((canonical_feature, fallback_value))

        for canonical_feature, content in extracted_items:
            display_name = f"Legal DB • {canonical_feature.replace('_', ' ').title()}"
            if nomor_putusan:
                display_name += f" • {nomor_putusan}"
            elif file_name:
                display_name += f" • {file_name}"

            context_vector: list[float] = []
            if extracted_vector:
                context_vector = extracted_vector
            elif embedding_function is not None:
                try:
                    embedded = _invoke_embedding(
                        embedding_function,
                        content,
                        prefix=RAG_EMBEDDING_CONTENT_PREFIX,
                        user=user,
                    )
                    embedded_vector = _convert_embedding(embedded)
                    if expected_vector_size and embedded_vector:
                        embedded_vector = _align_vector_dimensions(
                            embedded_vector, expected_vector_size
                        )
                    context_vector = _normalize_vector(embedded_vector)
                except Exception as exc:  # pragma: no cover - embedding dependent
                    log.debug(f"Failed to embed legal context content: {exc}")

            if context_vector:
                if expected_vector_size and len(context_vector) != expected_vector_size:
                    context_vector = _align_vector_dimensions(
                        context_vector, expected_vector_size
                    )
                    context_vector = _normalize_vector(context_vector)
                vectors.append(context_vector)

            metadata = {
                "source": nomor_putusan or file_name or canonical_feature,
                "collection_name": LEGAL_RAG_COLLECTION,
                "feature": canonical_feature,
                "file_name": file_name,
                "nomor_putusan": nomor_putusan,
                "document_id": document_id,
                "score": score,
                "name": display_name,
            }

            contexts.append(
                {
                    "source": {
                        "type": "legal_feature",
                        "id": f"{LEGAL_RAG_COLLECTION}:{document_id}:{canonical_feature}",
                        "name": display_name,
                        "collection": LEGAL_RAG_COLLECTION,
                        "feature": canonical_feature,
                    },
                    "document": [content],
                    "metadata": [metadata],
                    "distances": [[score]],
                }
            )

            if len(contexts) >= max_results:
                break

        if len(contexts) >= max_results:
            break

    aggregated_vector = _average_vectors(vectors)
    if expected_vector_size and aggregated_vector:
        aggregated_vector = _align_vector_dimensions(
            aggregated_vector, expected_vector_size
        )
        aggregated_vector = _normalize_vector(aggregated_vector)
    return contexts, aggregated_vector

def is_youtube_url(url: str) -> bool:
    youtube_regex = r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$"
    return re.match(youtube_regex, url) is not None


def get_loader(request, url: str):
    if is_youtube_url(url):
        return YoutubeLoader(
            url,
            language=request.app.state.config.YOUTUBE_LOADER_LANGUAGE,
            proxy_url=request.app.state.config.YOUTUBE_LOADER_PROXY_URL,
        )
    else:
        return get_web_loader(
            url,
            verify_ssl=request.app.state.config.ENABLE_WEB_LOADER_SSL_VERIFICATION,
            requests_per_second=request.app.state.config.WEB_LOADER_CONCURRENT_REQUESTS,
        )


def get_content_from_url(request, url: str) -> str:
    loader = get_loader(request, url)
    docs = loader.load()
    content = " ".join([doc.page_content for doc in docs])
    return content, docs


class VectorSearchRetriever(BaseRetriever):
    collection_name: Any
    embedding_function: Any
    top_k: int

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        result = VECTOR_DB_CLIENT.search(
            collection_name=self.collection_name,
            vectors=[self.embedding_function(query, RAG_EMBEDDING_QUERY_PREFIX)],
            limit=self.top_k,
        )

        ids = result.ids[0]
        metadatas = result.metadatas[0]
        documents = result.documents[0]

        results = []
        for idx in range(len(ids)):
            results.append(
                Document(
                    metadata=metadatas[idx],
                    page_content=documents[idx],
                )
            )
        return results


def query_doc(
    collection_name: str, query_embedding: list[float], k: int, user: UserModel = None
):
    try:
        log.debug(f"query_doc:doc {collection_name}")
        result = VECTOR_DB_CLIENT.search(
            collection_name=collection_name,
            vectors=[query_embedding],
            limit=k,
        )

        if result:
            log.info(f"query_doc:result {result.ids} {result.metadatas}")

        return result
    except Exception as e:
        log.exception(f"Error querying doc {collection_name} with limit {k}: {e}")
        raise e


def get_doc(collection_name: str, user: UserModel = None):
    try:
        log.debug(f"get_doc:doc {collection_name}")
        result = VECTOR_DB_CLIENT.get(collection_name=collection_name)

        if result:
            log.info(f"query_doc:result {result.ids} {result.metadatas}")

        return result
    except Exception as e:
        log.exception(f"Error getting doc {collection_name}: {e}")
        raise e


def query_doc_with_hybrid_search(
    collection_name: str,
    collection_result: GetResult,
    query: str,
    embedding_function,
    k: int,
    reranking_function,
    k_reranker: int,
    r: float,
    hybrid_bm25_weight: float,
) -> dict:
    try:
        if (
            not collection_result
            or not hasattr(collection_result, "documents")
            or not collection_result.documents
            or len(collection_result.documents) == 0
            or not collection_result.documents[0]
        ):
            log.warning(f"query_doc_with_hybrid_search:no_docs {collection_name}")
            return {"documents": [], "metadatas": [], "distances": []}

        log.debug(f"query_doc_with_hybrid_search:doc {collection_name}")

        bm25_retriever = BM25Retriever.from_texts(
            texts=collection_result.documents[0],
            metadatas=collection_result.metadatas[0],
        )
        bm25_retriever.k = k

        vector_search_retriever = VectorSearchRetriever(
            collection_name=collection_name,
            embedding_function=embedding_function,
            top_k=k,
        )

        if hybrid_bm25_weight <= 0:
            ensemble_retriever = EnsembleRetriever(
                retrievers=[vector_search_retriever], weights=[1.0]
            )
        elif hybrid_bm25_weight >= 1:
            ensemble_retriever = EnsembleRetriever(
                retrievers=[bm25_retriever], weights=[1.0]
            )
        else:
            ensemble_retriever = EnsembleRetriever(
                retrievers=[bm25_retriever, vector_search_retriever],
                weights=[hybrid_bm25_weight, 1.0 - hybrid_bm25_weight],
            )

        compressor = RerankCompressor(
            embedding_function=embedding_function,
            top_n=k_reranker,
            reranking_function=reranking_function,
            r_score=r,
        )

        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=ensemble_retriever
        )

        result = compression_retriever.invoke(query)

        distances = [d.metadata.get("score") for d in result]
        documents = [d.page_content for d in result]
        metadatas = [d.metadata for d in result]

        # retrieve only min(k, k_reranker) items, sort and cut by distance if k < k_reranker
        if k < k_reranker:
            sorted_items = sorted(
                zip(distances, metadatas, documents), key=lambda x: x[0], reverse=True
            )
            sorted_items = sorted_items[:k]

            if sorted_items:
                distances, documents, metadatas = map(list, zip(*sorted_items))
            else:
                distances, documents, metadatas = [], [], []

        result = {
            "distances": [distances],
            "documents": [documents],
            "metadatas": [metadatas],
        }

        log.info(
            "query_doc_with_hybrid_search:result "
            + f'{result["metadatas"]} {result["distances"]}'
        )
        return result
    except Exception as e:
        log.exception(f"Error querying doc {collection_name} with hybrid search: {e}")
        raise e


def merge_get_results(get_results: list[dict]) -> dict:
    # Initialize lists to store combined data
    combined_documents = []
    combined_metadatas = []
    combined_ids = []

    for data in get_results:
        combined_documents.extend(data["documents"][0])
        combined_metadatas.extend(data["metadatas"][0])
        combined_ids.extend(data["ids"][0])

    # Create the output dictionary
    result = {
        "documents": [combined_documents],
        "metadatas": [combined_metadatas],
        "ids": [combined_ids],
    }

    return result


def merge_and_sort_query_results(query_results: list[dict], k: int) -> dict:
    # Initialize lists to store combined data
    combined = dict()  # To store documents with unique document hashes

    for data in query_results:
        distances = data["distances"][0]
        documents = data["documents"][0]
        metadatas = data["metadatas"][0]

        for distance, document, metadata in zip(distances, documents, metadatas):
            if isinstance(document, str):
                doc_hash = hashlib.sha256(
                    document.encode()
                ).hexdigest()  # Compute a hash for uniqueness

                if doc_hash not in combined.keys():
                    combined[doc_hash] = (distance, document, metadata)
                    continue  # if doc is new, no further comparison is needed

                # if doc is alredy in, but new distance is better, update
                if distance > combined[doc_hash][0]:
                    combined[doc_hash] = (distance, document, metadata)

    combined = list(combined.values())
    # Sort the list based on distances
    combined.sort(key=lambda x: x[0], reverse=True)

    # Slice to keep only the top k elements
    sorted_distances, sorted_documents, sorted_metadatas = (
        zip(*combined[:k]) if combined else ([], [], [])
    )

    # Create and return the output dictionary
    return {
        "distances": [list(sorted_distances)],
        "documents": [list(sorted_documents)],
        "metadatas": [list(sorted_metadatas)],
    }


def get_all_items_from_collections(collection_names: list[str]) -> dict:
    results = []

    for collection_name in collection_names:
        if collection_name:
            try:
                result = get_doc(collection_name=collection_name)
                if result is not None:
                    results.append(result.model_dump())
            except Exception as e:
                log.exception(f"Error when querying the collection: {e}")
        else:
            pass

    return merge_get_results(results)


def query_collection(
    collection_names: list[str],
    queries: list[str],
    embedding_function,
    k: int,
) -> dict:
    results = []
    error = False

    def process_query_collection(collection_name, query_embedding):
        try:
            if collection_name:
                result = query_doc(
                    collection_name=collection_name,
                    k=k,
                    query_embedding=query_embedding,
                )
                if result is not None:
                    return result.model_dump(), None
            return None, None
        except Exception as e:
            log.exception(f"Error when querying the collection: {e}")
            return None, e

    # Generate all query embeddings (in one call)
    query_embeddings = embedding_function(queries, prefix=RAG_EMBEDDING_QUERY_PREFIX)
    log.debug(
        f"query_collection: processing {len(queries)} queries across {len(collection_names)} collections"
    )

    with ThreadPoolExecutor() as executor:
        future_results = []
        for query_embedding in query_embeddings:
            for collection_name in collection_names:
                result = executor.submit(
                    process_query_collection, collection_name, query_embedding
                )
                future_results.append(result)
        task_results = [future.result() for future in future_results]

    for result, err in task_results:
        if err is not None:
            error = True
        elif result is not None:
            results.append(result)

    if error and not results:
        log.warning("All collection queries failed. No results returned.")

    return merge_and_sort_query_results(results, k=k)


def query_collection_with_hybrid_search(
    collection_names: list[str],
    queries: list[str],
    embedding_function,
    k: int,
    reranking_function,
    k_reranker: int,
    r: float,
    hybrid_bm25_weight: float,
) -> dict:
    results = []
    error = False
    # Fetch collection data once per collection sequentially
    # Avoid fetching the same data multiple times later
    collection_results = {}
    for collection_name in collection_names:
        try:
            log.debug(
                f"query_collection_with_hybrid_search:VECTOR_DB_CLIENT.get:collection {collection_name}"
            )
            collection_results[collection_name] = VECTOR_DB_CLIENT.get(
                collection_name=collection_name
            )
        except Exception as e:
            log.exception(f"Failed to fetch collection {collection_name}: {e}")
            collection_results[collection_name] = None

    log.info(
        f"Starting hybrid search for {len(queries)} queries in {len(collection_names)} collections..."
    )

    def process_query(collection_name, query):
        try:
            result = query_doc_with_hybrid_search(
                collection_name=collection_name,
                collection_result=collection_results[collection_name],
                query=query,
                embedding_function=embedding_function,
                k=k,
                reranking_function=reranking_function,
                k_reranker=k_reranker,
                r=r,
                hybrid_bm25_weight=hybrid_bm25_weight,
            )
            return result, None
        except Exception as e:
            log.exception(f"Error when querying the collection with hybrid_search: {e}")
            return None, e

    # Prepare tasks for all collections and queries
    # Avoid running any tasks for collections that failed to fetch data (have assigned None)
    tasks = [
        (cn, q)
        for cn in collection_names
        if collection_results[cn] is not None
        for q in queries
    ]

    with ThreadPoolExecutor() as executor:
        future_results = [executor.submit(process_query, cn, q) for cn, q in tasks]
        task_results = [future.result() for future in future_results]

    for result, err in task_results:
        if err is not None:
            error = True
        elif result is not None:
            results.append(result)

    if error and not results:
        raise Exception(
            "Hybrid search failed for all collections. Using Non-hybrid search as fallback."
        )

    return merge_and_sort_query_results(results, k=k)


def get_embedding_function(
    embedding_engine,
    embedding_model,
    embedding_function,
    url,
    key,
    embedding_batch_size,
    azure_api_version=None,
):
    if embedding_engine == "":
        return lambda query, prefix=None, user=None: embedding_function.encode(
            query, **({"prompt": prefix} if prefix else {})
        ).tolist()
    elif embedding_engine in ["ollama", "openai", "azure_openai"]:
        func = lambda query, prefix=None, user=None: generate_embeddings(
            engine=embedding_engine,
            model=embedding_model,
            text=query,
            prefix=prefix,
            url=url,
            key=key,
            user=user,
            azure_api_version=azure_api_version,
        )

        def generate_multiple(query, prefix, user, func):
            if isinstance(query, list):
                embeddings = []
                for i in range(0, len(query), embedding_batch_size):
                    batch_embeddings = func(
                        query[i : i + embedding_batch_size],
                        prefix=prefix,
                        user=user,
                    )

                    if isinstance(batch_embeddings, list):
                        embeddings.extend(batch_embeddings)
                return embeddings
            else:
                return func(query, prefix, user)

        return lambda query, prefix=None, user=None: generate_multiple(
            query, prefix, user, func
        )
    else:
        raise ValueError(f"Unknown embedding engine: {embedding_engine}")


def get_reranking_function(reranking_engine, reranking_model, reranking_function):
    if reranking_function is None:
        return None
    if reranking_engine == "external":
        return lambda sentences, user=None: reranking_function.predict(
            sentences, user=user
        )
    else:
        return lambda sentences, user=None: reranking_function.predict(sentences)


def get_sources_from_items(
    request,
    items,
    queries,
    embedding_function,
    k,
    reranking_function,
    k_reranker,
    r,
    hybrid_bm25_weight,
    hybrid_search,
    full_context=False,
    user: Optional[UserModel] = None,
):
    log.debug(
        f"items: {items} {queries} {embedding_function} {reranking_function} {full_context}"
    )

    extracted_collections = []
    query_results = []

    for item in items:
        query_result = None
        collection_names = []

        if item.get("type") == "text":
            # Raw Text
            # Used during temporary chat file uploads or web page & youtube attachements

            if item.get("context") == "full":
                if item.get("file"):
                    # if item has file data, use it
                    query_result = {
                        "documents": [
                            [item.get("file", {}).get("data", {}).get("content")]
                        ],
                        "metadatas": [[item.get("file", {}).get("meta", {})]],
                    }

            if query_result is None:
                # Fallback
                if item.get("collection_name"):
                    # If item has a collection name, use it
                    collection_names.append(item.get("collection_name"))
                elif item.get("file"):
                    # If item has file data, use it
                    query_result = {
                        "documents": [
                            [item.get("file", {}).get("data", {}).get("content")]
                        ],
                        "metadatas": [[item.get("file", {}).get("meta", {})]],
                    }
                else:
                    # Fallback to item content
                    query_result = {
                        "documents": [[item.get("content")]],
                        "metadatas": [
                            [{"file_id": item.get("id"), "name": item.get("name")}]
                        ],
                    }

        elif item.get("type") == "note":
            # Note Attached
            note = Notes.get_note_by_id(item.get("id"))

            if note and (
                user.role == "admin"
                or note.user_id == user.id
                or has_access(user.id, "read", note.access_control)
            ):
                # User has access to the note
                query_result = {
                    "documents": [[note.data.get("content", {}).get("md", "")]],
                    "metadatas": [[{"file_id": note.id, "name": note.title}]],
                }

        elif item.get("type") == "chat":
            # Chat Attached
            chat = Chats.get_chat_by_id(item.get("id"))

            if chat and (user.role == "admin" or chat.user_id == user.id):
                messages_map = chat.chat.get("history", {}).get("messages", {})
                message_id = chat.chat.get("history", {}).get("currentId")

                if messages_map and message_id:
                    # Reconstruct the message list in order
                    message_list = get_message_list(messages_map, message_id)
                    message_history = "\n".join(
                        [
                            f"#### {m.get('role', 'user').capitalize()}\n{m.get('content')}\n"
                            for m in message_list
                        ]
                    )

                    # User has access to the chat
                    query_result = {
                        "documents": [[message_history]],
                        "metadatas": [[{"file_id": chat.id, "name": chat.title}]],
                    }

        elif item.get("type") == "url":
            content, docs = get_content_from_url(request, item.get("url"))
            if docs:
                query_result = {
                    "documents": [[content]],
                    "metadatas": [[{"url": item.get("url"), "name": item.get("url")}]],
                }
        elif item.get("type") == "file":
            file_metadata = {
                "file_id": item.get("id"),
                "name": item.get("name"),
            }
            file_content = item.get("file", {}).get("data", {}).get("content", "")

            if not file_content and item.get("id"):
                file_object = Files.get_file_by_id(item.get("id"))
                if file_object:
                    file_content = file_object.data.get("content", "")
                    file_metadata = {
                        "file_id": item.get("id"),
                        "name": file_object.filename,
                        "source": file_object.filename,
                        **file_object.data.get("metadata", {}),
                    }
            else:
                file_metadata.update(
                    item.get("file", {}).get("data", {}).get("metadata", {})
                )

            if file_content:
                query_result = {
                    "documents": [[file_content]],
                    "metadatas": [[file_metadata]],
                }
            else:
                # Fall back to the original chunking + vector search flow only when
                # no extracted content is available. Keep this behaviour so we never
                # drop a file silently, but prefer the direct full-text response above.
                if item.get("legacy"):
                    collection_names.append(f"{item['id']}")
                else:
                    collection_names.append(f"file-{item['id']}")

        elif item.get("type") == "collection":
            if (
                item.get("context") == "full"
                or request.app.state.config.BYPASS_EMBEDDING_AND_RETRIEVAL
            ):
                # Manual Full Mode Toggle for Collection
                knowledge_base = Knowledges.get_knowledge_by_id(item.get("id"))

                if knowledge_base and (
                    user.role == "admin"
                    or knowledge_base.user_id == user.id
                    or has_access(user.id, "read", knowledge_base.access_control)
                ):

                    file_ids = knowledge_base.data.get("file_ids", [])

                    documents = []
                    metadatas = []
                    for file_id in file_ids:
                        file_object = Files.get_file_by_id(file_id)

                        if file_object:
                            documents.append(file_object.data.get("content", ""))
                            metadatas.append(
                                {
                                    "file_id": file_id,
                                    "name": file_object.filename,
                                    "source": file_object.filename,
                                }
                            )

                    query_result = {
                        "documents": [documents],
                        "metadatas": [metadatas],
                    }
            else:
                # Fallback to collection names
                if item.get("legacy"):
                    collection_names = item.get("collection_names", [])
                else:
                    collection_names.append(item["id"])

        elif item.get("docs"):
            # BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL
            query_result = {
                "documents": [[doc.get("content") for doc in item.get("docs")]],
                "metadatas": [[doc.get("metadata") for doc in item.get("docs")]],
            }
        elif item.get("collection_name"):
            # Direct Collection Name
            collection_names.append(item["collection_name"])
        elif item.get("collection_names"):
            # Collection Names List
            collection_names.extend(item["collection_names"])

        # If query_result is None
        # Fallback to collection names and vector search the collections
        if query_result is None and collection_names:
            collection_names = set(collection_names).difference(extracted_collections)
            if not collection_names:
                log.debug(f"skipping {item} as it has already been extracted")
                continue

            try:
                if full_context:
                    query_result = get_all_items_from_collections(collection_names)
                else:
                    query_result = None  # Initialize to None
                    if hybrid_search:
                        try:
                            query_result = query_collection_with_hybrid_search(
                                collection_names=collection_names,
                                queries=queries,
                                embedding_function=embedding_function,
                                k=k,
                                reranking_function=reranking_function,
                                k_reranker=k_reranker,
                                r=r,
                                hybrid_bm25_weight=hybrid_bm25_weight,
                            )
                        except Exception as e:
                            log.debug(
                                "Error when using hybrid search, using non hybrid search as fallback."
                            )

                    # fallback to non-hybrid search
                    if not hybrid_search and query_result is None:
                        query_result = query_collection(
                            collection_names=collection_names,
                            queries=queries,
                            embedding_function=embedding_function,
                            k=k,
                        )
            except Exception as e:
                log.exception(e)

            extracted_collections.extend(collection_names)

        if query_result:
            if "data" in item:
                del item["data"]
            query_results.append({**query_result, "file": item})

    sources = []
    legal_sources: list[dict] = []
    aggregated_feature_vector: list[float] = []

    if LEGAL_RAG_COLLECTION:
        try:
            max_results = LEGAL_RAG_MAX_RESULTS
            if isinstance(k, int) and k > 0:
                max_results = min(LEGAL_RAG_MAX_RESULTS, k)

            legal_sources, aggregated_feature_vector = _legal_feature_contexts(
                queries=queries,
                embedding_function=embedding_function,
                user=user,
                max_results=max_results,
            )
        except Exception as exc:
            log.debug(f"Legal context retrieval failed: {exc}")
            legal_sources = []
            aggregated_feature_vector = []

    if aggregated_feature_vector:
        for query_result in query_results:
            documents_list = query_result.get("documents") or []
            metadatas_list = query_result.get("metadatas") or []

            if not documents_list or not documents_list[0]:
                continue

            documents = documents_list[0]
            metadata_entries = metadatas_list[0] if metadatas_list else []

            try:
                embeddings = _embed_texts(
                    embedding_function,
                    documents,
                    user=user,
                )
            except Exception as exc:
                log.debug(f"Failed to embed documents for re-ranking: {exc}")
                continue

            if not embeddings:
                continue

            scores = _cosine_scores(embeddings, aggregated_feature_vector)

            combined = []
            for idx, (score, document) in enumerate(zip(scores, documents)):
                metadata = (
                    metadata_entries[idx]
                    if idx < len(metadata_entries)
                    else metadata_entries[-1]
                    if metadata_entries
                    else {}
                )
                combined.append((score, document, metadata))

            combined.sort(key=lambda item: item[0], reverse=True)
            if isinstance(k, int) and k > 0:
                combined = combined[:k]

            if not combined:
                continue

            query_result["documents"] = [[item[1] for item in combined]]
            query_result["metadatas"] = [[item[2] for item in combined]]
            query_result["distances"] = [[float(item[0]) for item in combined]]

    sources.extend(legal_sources)
    for query_result in query_results:
        try:
            if "documents" in query_result:
                if "metadatas" in query_result:
                    source = {
                        "source": query_result["file"],
                        "document": query_result["documents"][0],
                        "metadata": query_result["metadatas"][0],
                    }
                    if "distances" in query_result and query_result["distances"]:
                        source["distances"] = query_result["distances"][0]

                    sources.append(source)
        except Exception as e:
            log.exception(e)
    return sources


def get_model_path(model: str, update_model: bool = False):
    # Construct huggingface_hub kwargs with local_files_only to return the snapshot path
    cache_dir = os.getenv("SENTENCE_TRANSFORMERS_HOME")

    local_files_only = not update_model

    if OFFLINE_MODE:
        local_files_only = True

    snapshot_kwargs = {
        "cache_dir": cache_dir,
        "local_files_only": local_files_only,
    }

    log.debug(f"model: {model}")
    log.debug(f"snapshot_kwargs: {snapshot_kwargs}")

    # Inspiration from upstream sentence_transformers
    if (
        os.path.exists(model)
        or ("\\" in model or model.count("/") > 1)
        and local_files_only
    ):
        # If fully qualified path exists, return input, else set repo_id
        return model
    elif "/" not in model:
        # Set valid repo_id for model short-name
        model = "sentence-transformers" + "/" + model

    snapshot_kwargs["repo_id"] = model

    # Attempt to query the huggingface_hub library to determine the local path and/or to update
    try:
        model_repo_path = snapshot_download(**snapshot_kwargs)
        log.debug(f"model_repo_path: {model_repo_path}")
        return model_repo_path
    except Exception as e:
        log.exception(f"Cannot determine model snapshot path: {e}")
        return model


def generate_openai_batch_embeddings(
    model: str,
    texts: list[str],
    url: str = "https://api.openai.com/v1",
    key: str = "",
    prefix: str = None,
    user: UserModel = None,
) -> Optional[list[list[float]]]:
    try:
        log.debug(
            f"generate_openai_batch_embeddings:model {model} batch size: {len(texts)}"
        )
        json_data = {"input": texts, "model": model}
        if isinstance(RAG_EMBEDDING_PREFIX_FIELD_NAME, str) and isinstance(prefix, str):
            json_data[RAG_EMBEDDING_PREFIX_FIELD_NAME] = prefix

        r = requests.post(
            f"{url}/embeddings",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                **(
                    {
                        "X-OpenWebUI-User-Name": quote(user.name, safe=" "),
                        "X-OpenWebUI-User-Id": user.id,
                        "X-OpenWebUI-User-Email": user.email,
                        "X-OpenWebUI-User-Role": user.role,
                    }
                    if ENABLE_FORWARD_USER_INFO_HEADERS and user
                    else {}
                ),
            },
            json=json_data,
        )
        r.raise_for_status()
        data = r.json()
        if "data" in data:
            return [elem["embedding"] for elem in data["data"]]
        else:
            raise "Something went wrong :/"
    except Exception as e:
        log.exception(f"Error generating openai batch embeddings: {e}")
        return None


def generate_azure_openai_batch_embeddings(
    model: str,
    texts: list[str],
    url: str,
    key: str = "",
    version: str = "",
    prefix: str = None,
    user: UserModel = None,
) -> Optional[list[list[float]]]:
    try:
        log.debug(
            f"generate_azure_openai_batch_embeddings:deployment {model} batch size: {len(texts)}"
        )
        json_data = {"input": texts}
        if isinstance(RAG_EMBEDDING_PREFIX_FIELD_NAME, str) and isinstance(prefix, str):
            json_data[RAG_EMBEDDING_PREFIX_FIELD_NAME] = prefix

        url = f"{url}/openai/deployments/{model}/embeddings?api-version={version}"

        for _ in range(5):
            r = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "api-key": key,
                    **(
                        {
                            "X-OpenWebUI-User-Name": quote(user.name, safe=" "),
                            "X-OpenWebUI-User-Id": user.id,
                            "X-OpenWebUI-User-Email": user.email,
                            "X-OpenWebUI-User-Role": user.role,
                        }
                        if ENABLE_FORWARD_USER_INFO_HEADERS and user
                        else {}
                    ),
                },
                json=json_data,
            )
            if r.status_code == 429:
                retry = float(r.headers.get("Retry-After", "1"))
                time.sleep(retry)
                continue
            r.raise_for_status()
            data = r.json()
            if "data" in data:
                return [elem["embedding"] for elem in data["data"]]
            else:
                raise Exception("Something went wrong :/")
        return None
    except Exception as e:
        log.exception(f"Error generating azure openai batch embeddings: {e}")
        return None


def generate_ollama_batch_embeddings(
    model: str,
    texts: list[str],
    url: str,
    key: str = "",
    prefix: str = None,
    user: UserModel = None,
) -> Optional[list[list[float]]]:
    try:
        log.debug(
            f"generate_ollama_batch_embeddings:model {model} batch size: {len(texts)}"
        )
        json_data = {"input": texts, "model": model}
        if isinstance(RAG_EMBEDDING_PREFIX_FIELD_NAME, str) and isinstance(prefix, str):
            json_data[RAG_EMBEDDING_PREFIX_FIELD_NAME] = prefix

        r = requests.post(
            f"{url}/api/embed",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                **(
                    {
                        "X-OpenWebUI-User-Name": quote(user.name, safe=" "),
                        "X-OpenWebUI-User-Id": user.id,
                        "X-OpenWebUI-User-Email": user.email,
                        "X-OpenWebUI-User-Role": user.role,
                    }
                    if ENABLE_FORWARD_USER_INFO_HEADERS
                    else {}
                ),
            },
            json=json_data,
        )
        r.raise_for_status()
        data = r.json()

        if "embeddings" in data:
            return data["embeddings"]
        else:
            raise "Something went wrong :/"
    except Exception as e:
        log.exception(f"Error generating ollama batch embeddings: {e}")
        return None


def generate_embeddings(
    engine: str,
    model: str,
    text: Union[str, list[str]],
    prefix: Union[str, None] = None,
    **kwargs,
):
    url = kwargs.get("url", "")
    key = kwargs.get("key", "")
    user = kwargs.get("user")

    if prefix is not None and RAG_EMBEDDING_PREFIX_FIELD_NAME is None:
        if isinstance(text, list):
            text = [f"{prefix}{text_element}" for text_element in text]
        else:
            text = f"{prefix}{text}"

    if engine == "ollama":
        embeddings = generate_ollama_batch_embeddings(
            **{
                "model": model,
                "texts": text if isinstance(text, list) else [text],
                "url": url,
                "key": key,
                "prefix": prefix,
                "user": user,
            }
        )
        return embeddings[0] if isinstance(text, str) else embeddings
    elif engine == "openai":
        embeddings = generate_openai_batch_embeddings(
            model, text if isinstance(text, list) else [text], url, key, prefix, user
        )
        return embeddings[0] if isinstance(text, str) else embeddings
    elif engine == "azure_openai":
        azure_api_version = kwargs.get("azure_api_version", "")
        embeddings = generate_azure_openai_batch_embeddings(
            model,
            text if isinstance(text, list) else [text],
            url,
            key,
            azure_api_version,
            prefix,
            user,
        )
        return embeddings[0] if isinstance(text, str) else embeddings


import operator

from langchain_core.callbacks import Callbacks
from langchain_core.documents import BaseDocumentCompressor, Document


class RerankCompressor(BaseDocumentCompressor):
    embedding_function: Any
    top_n: int
    reranking_function: Any
    r_score: float

    class Config:
        extra = "forbid"
        arbitrary_types_allowed = True

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        reranking = self.reranking_function is not None

        scores = None
        if reranking:
            scores = self.reranking_function(
                [(query, doc.page_content) for doc in documents]
            )
        else:
            from sentence_transformers import util

            query_embedding = self.embedding_function(query, RAG_EMBEDDING_QUERY_PREFIX)
            document_embedding = self.embedding_function(
                [doc.page_content for doc in documents], RAG_EMBEDDING_CONTENT_PREFIX
            )
            scores = util.cos_sim(query_embedding, document_embedding)[0]

        if scores is not None:
            docs_with_scores = list(
                zip(
                    documents,
                    scores.tolist() if not isinstance(scores, list) else scores,
                )
            )
            if self.r_score:
                docs_with_scores = [
                    (d, s) for d, s in docs_with_scores if s >= self.r_score
                ]

            result = sorted(docs_with_scores, key=operator.itemgetter(1), reverse=True)
            final_results = []
            for doc, doc_score in result[: self.top_n]:
                metadata = doc.metadata
                metadata["score"] = doc_score
                doc = Document(
                    page_content=doc.page_content,
                    metadata=metadata,
                )
                final_results.append(doc)
            return final_results
        else:
            log.warning(
                "No valid scores found, check your reranking function. Returning original documents."
            )
            return documents
