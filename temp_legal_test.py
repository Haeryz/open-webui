import sys
sys.path.append(r'd:\Side\KY-Web\open-webui\backend')
import open_webui.env  # noqa: F401 to ensure .env is loaded
from sentence_transformers import SentenceTransformer
from open_webui import config as cfg
from open_webui.retrieval.utils import _legal_feature_contexts


model = SentenceTransformer(cfg.RAG_EMBEDDING_MODEL.value)


def embedding_fn(text, prefix=None, user=None):
    if isinstance(text, list):
        return model.encode(text, normalize_embeddings=False).tolist()
    return model.encode(text, normalize_embeddings=False).tolist()


queries = ['Ekstrak amar putusan', 'Saya butuh amar putusan terbaru']
contexts, aggregated = _legal_feature_contexts(
    queries,
    embedding_function=embedding_fn,
    user=None,
    max_results=3,
)

print('num contexts', len(contexts))
for ctx in contexts:
    meta = ctx['metadata'][0]
    snippet = ctx['document'][0][:120]
    print(meta['feature'], meta.get('nomor_putusan'), snippet)
print('aggregated vector length', len(aggregated))
