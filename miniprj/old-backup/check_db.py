"""
Quick test to check if the markdown-based vector DB was created successfully
"""
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

HF_MODEL = "BAAI/bge-m3"
MARKDOWN_PERSIST_DIR = "./db_medical_md"
MARKDOWN_COLLECTION = "medical_guidelines_markdown"

print("Checking markdown-based vector DB...")

try:
    # Load embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name=HF_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    
    # Try to load vector store
    vectorstore = Chroma(
        persist_directory=MARKDOWN_PERSIST_DIR,
        collection_name=MARKDOWN_COLLECTION,
        embedding_function=embeddings,
    )
    
    # Get collection info
    collection = vectorstore._collection
    count = collection.count()
    
    print(f"✅ Vector store loaded successfully!")
    print(f"   Collection: {MARKDOWN_COLLECTION}")
    print(f"   Document count: {count}")
    
    if count > 0:
        # Try a sample query
        results = vectorstore.similarity_search("패혈증", k=1)
        if results:
            print(f"\n✅ Sample query works!")
            print(f"   Section path: {results[0].metadata.get('section_path', 'N/A')}")
            print(f"   Content preview: {results[0].page_content[:100]}...")
    else:
        print("⚠️  Vector store exists but is empty")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nVector DB was not created successfully. Need to run rag_markdown.py again.")
