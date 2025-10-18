import sys
sys.path.append(r'd:\Side\KY-Web\open-webui\backend')
import open_webui.config as cfg
from qdrant_client import QdrantClient

client = QdrantClient(url=cfg.QDRANT_URI, api_key=cfg.QDRANT_API_KEY, timeout=15)

offset = None
found = []
max_pages = 500
for _ in range(max_pages):
    points, offset = client.scroll(
        collection_name='LEGAL_RAG_TEST',
        with_payload=True,
        with_vectors=False,
        limit=1,
        offset=offset,
    )
    for point in points:
        payload = point.payload or {}
        if (payload.get('source_column') or '').lower() == 'amar_putusan':
            snippet = (payload.get('column_value') or '')
            found.append(
                {
                    'nomor_putusan': payload.get('nomor_putusan'),
                    'document_id': payload.get('document_id'),
                    'snippet': snippet,
                }
            )
            if len(found) >= 3:
                break
    if len(found) >= 3 or not offset:
        break

print('found', len(found))
for item in found:
    print('nomor_putusan:', item['nomor_putusan'])
    print('document_id:', item['document_id'])
    print('snippet:', item['snippet'][:200])
    print('-' * 40)
