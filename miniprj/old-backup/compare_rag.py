"""
Compare RAG retrieval quality between original and markdown-based chunking
"""
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

# Configuration
HF_MODEL = "BAAI/bge-m3"

# Original RAG
ORIGINAL_PERSIST_DIR = "./db_medical"
ORIGINAL_COLLECTION = "medical_guidelines"

# Markdown-based RAG
MARKDOWN_PERSIST_DIR = "./db_medical_md"
MARKDOWN_COLLECTION = "medical_guidelines_markdown"


def load_vectorstore(persist_dir: str, collection_name: str) -> Chroma:
    """Load vector store"""
    embeddings = HuggingFaceEmbeddings(
        model_name=HF_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    
    return Chroma(
        persist_directory=persist_dir,
        collection_name=collection_name,
        embedding_function=embeddings,
    )


def search_and_display(vectorstore: Chroma, query: str, k: int = 3, label: str = ""):
    """Search and display results"""
    print(f"\n{'=' * 80}")
    print(f"{label}")
    print(f"{'=' * 80}")
    
    results = vectorstore.similarity_search(query, k=k)
    
    for i, doc in enumerate(results, 1):
        print(f"\n[Result {i}]")
        print(f"Source: {doc.metadata.get('source', 'N/A')}")
        print(f"Page: {doc.metadata.get('page', 'N/A')}")
        
        # Show structure info if available (markdown-based)
        if 'section_path' in doc.metadata:
            print(f"Section: {doc.metadata['section_path']}")
            print(f"Heading Level: {doc.metadata.get('heading_level', 'N/A')}")
        
        # Content preview
        content = doc.page_content
        preview_length = 400
        if len(content) > preview_length:
            preview = content[:preview_length] + "..."
        else:
            preview = content
        
        print(f"\nContent:\n{preview}")
        print("-" * 80)


def compare_retrieval(original_db: Chroma, markdown_db: Chroma, query: str, k: int = 3):
    """Compare retrieval results side by side"""
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)
    
    search_and_display(original_db, query, k=k, label="🔵 ORIGINAL (RecursiveCharacterTextSplitter)")
    search_and_display(markdown_db, query, k=k, label="🟢 MARKDOWN (Structure-Aware Chunking)")


def main():
    print("=" * 80)
    print("RAG Comparison: Original vs Markdown-Based Chunking")
    print("=" * 80)
    
    # Load both vector stores
    print("\n[Loading vector stores...]")
    
    try:
        original_db = load_vectorstore(ORIGINAL_PERSIST_DIR, ORIGINAL_COLLECTION)
        print(f"✓ Loaded original DB: {ORIGINAL_PERSIST_DIR}")
    except Exception as e:
        print(f"✗ Failed to load original DB: {e}")
        print("  Run 'python rag.py' first to create the original vector store")
        return
    
    try:
        markdown_db = load_vectorstore(MARKDOWN_PERSIST_DIR, MARKDOWN_COLLECTION)
        print(f"✓ Loaded markdown DB: {MARKDOWN_PERSIST_DIR}")
    except Exception as e:
        print(f"✗ Failed to load markdown DB: {e}")
        print("  Run 'python rag_markdown.py' first to create the markdown vector store")
        return
    
    # Test queries
    test_queries = [
        "패혈증 환자의 초기 수액 소생술 권고사항은?",
        "승압제 투여 시 목표 MAP은?",
        "기계환기 설정 시 일회 호흡량은?",
        "패혈증 초기 번들 치료는?",
    ]
    
    print("\n" + "=" * 80)
    print("Running comparison tests...")
    print("=" * 80)
    
    for query in test_queries:
        compare_retrieval(original_db, markdown_db, query, k=3)
        print("\n" * 2)
    
    print("=" * 80)
    print("✅ Comparison complete!")
    print("=" * 80)
    print("\n💡 Analysis Guidelines:")
    print("  - Check if markdown-based results have better context")
    print("  - Look for section_path metadata in markdown results")
    print("  - Compare if chunks are semantically more complete")
    print("  - Verify if relevant information is better preserved")


if __name__ == "__main__":
    main()
