import chromadb

client = chromadb.PersistentClient(path="db_medical")
col = client.get_or_create_collection("medical_guidelines")  # 본인 컬렉션명으로 변경

peek = col.peek(5)
print(peek["metadatas"])