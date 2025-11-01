import sys
from collections import defaultdict

sys.path.append(r'd:\Side\KY-Web\open-webui\backend')
import open_webui.env  # noqa: F401

from sentence_transformers import SentenceTransformer
from open_webui import config as cfg
from open_webui.retrieval.utils import _legal_feature_contexts


model = SentenceTransformer(cfg.RAG_EMBEDDING_MODEL.value)


def embedding_fn(text, prefix=None, user=None):
    if isinstance(text, list):
        return model.encode(text, normalize_embeddings=False).tolist()
    return model.encode(text, normalize_embeddings=False).tolist()


def run_test_case(name, queries):
    contexts, aggregated = _legal_feature_contexts(
        queries,
        embedding_function=embedding_fn,
        user=None,
        max_results=3,
    )

    unique_sources = set()
    grouped_features = defaultdict(set)
    print(f"\n>>> Test Case: {name}")
    print(f"Queries: {queries}")
    print(f"Returned contexts: {len(contexts)}")
    for idx, ctx in enumerate(contexts, start=1):
        metadata = ctx['metadata'][0]
        feature = metadata.get('feature')
        nomor_putusan = metadata.get('nomor_putusan')
        source = metadata.get('source')
        unique_sources.add(source)
        if feature:
            grouped_features[feature].add(nomor_putusan or 'N/A')
        snippet = ctx['document'][0][:120]
        print(f"  [{idx}] feature={feature} nomor_putusan={nomor_putusan} source={source}")
        print(f"       snippet={snippet}")
    print(f"Unique sources: {len(unique_sources)} -> {sorted(unique_sources)}")
    print(f"Feature coverage: {{feature: sorted(list(ids)) for feature, ids in grouped_features.items()}}")
    print(f"Aggregated vector length: {len(aggregated)}")


TEST_CASES = {
    "amar_putusan": ['Ekstrak amar putusan', 'Saya butuh amar putusan terbaru'],
    "pidana": ['Ekstrak pidana', 'Butuh sanksi pidana terbaru'],
    "perdata": ['Ekstrak amar gugatan perdata', 'Saya perlu putusan perdata terbaru'],
}

if __name__ == '__main__':
    for name, queries in TEST_CASES.items():
        run_test_case(name, queries)
