import chromadb

client = chromadb.PersistentClient(path='ravi_chroma_db')
col = client.get_collection('ravi_knowledge')

to_delete = [
    'test_001',
    '5704b13c-3514-4106-978d-4037f0a52676',
    '3fee63cd-7f95-4eb1-b7e6-4a995e9ed190',
    'ravi_knowledge_1773430596916'
]

col.delete(ids=to_delete)
print(f"Deleted {len(to_delete)} items. Remaining: {col.count()}")
