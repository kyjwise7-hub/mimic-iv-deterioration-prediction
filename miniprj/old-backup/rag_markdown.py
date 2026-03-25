import os
import glob
import re
from typing import List, Dict
from dataclasses import dataclass

try:
    import pymupdf4llm
except ImportError:
    print("⚠️  pymupdf4llm not installed. Run: pip install pymupdf4llm")
    pymupdf4llm = None

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


# Configuration
LOCAL_EMBED_MODEL = "BAAI/bge-m3"
PDF_FOLDER = "./guidelines"
PERSIST_DIR = "./db_medical_md"  # Different DB for comparison
COLLECTION_NAME = "medical_guidelines_markdown"

# Chunking parameters
MAX_CHUNK_SIZE = 1500  # Slightly larger since we're chunking by section
MIN_CHUNK_SIZE = 200   # Minimum viable chunk size


@dataclass
class MarkdownSection:
    """Represents a hierarchical section in the markdown document"""
    level: int
    title: str
    content: str
    start_page: int
    end_page: int
    parent_path: str = ""
    
    @property
    def section_path(self) -> str:
        """Get full hierarchical path"""
        if self.parent_path:
            return f"{self.parent_path} > {self.title}"
        return self.title


def pdf_to_markdown(pdf_path: str) -> tuple[str, Dict]:
    """
    Convert PDF to Markdown using pymupdf4llm
    
    Returns:
        tuple: (markdown_text, metadata)
    """
    if pymupdf4llm is None:
        raise ImportError("pymupdf4llm is required. Install with: pip install pymupdf4llm")
    
    # Extract markdown with page references
    md_text = pymupdf4llm.to_markdown(
        pdf_path,
        page_chunks=False,  # We'll do our own chunking
        write_images=False,  # Don't extract images for RAG
        show_progress=False,
    )
    
    metadata = {
        "source": os.path.basename(pdf_path),
        "conversion_method": "pymupdf4llm"
    }
    
    return md_text, metadata


def extract_sections_from_markdown(md_text: str, source_metadata: Dict) -> List[MarkdownSection]:
    """
    Extract hierarchical sections from markdown text
    
    Identifies headers and creates structured sections with parent-child relationships
    """
    sections = []
    lines = md_text.split('\n')
    
    current_section = None
    content_buffer = []
    header_stack = []  # Track parent headers for hierarchy
    current_page = 1
    
    # Pattern to detect page markers (if present from pymupdf4llm)
    page_pattern = re.compile(r'<!---\s*Page\s+(\d+)\s*--->', re.IGNORECASE)
    
    for line in lines:
        # Check for page markers
        page_match = page_pattern.search(line)
        if page_match:
            current_page = int(page_match.group(1))
            continue
        
        # Check for markdown headers
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        
        if header_match:
            # Save previous section if exists
            if current_section and content_buffer:
                current_section.content = '\n'.join(content_buffer).strip()
                if len(current_section.content) >= MIN_CHUNK_SIZE:
                    sections.append(current_section)
                content_buffer = []
            
            # Parse new header
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            
            # Update header stack for hierarchy
            header_stack = header_stack[:level-1]  # Remove deeper levels
            if len(header_stack) < level:
                header_stack.append(title)
            else:
                header_stack[level-1] = title
            
            # Build parent path
            parent_path = ' > '.join(header_stack[:-1]) if len(header_stack) > 1 else ""
            
            # Create new section
            current_section = MarkdownSection(
                level=level,
                title=title,
                content="",
                start_page=current_page,
                end_page=current_page,
                parent_path=parent_path
            )
            
            # Add header to content
            content_buffer.append(line)
        else:
            # Add to content buffer
            if line.strip():  # Skip empty lines at boundaries
                content_buffer.append(line)
                if current_section:
                    current_section.end_page = current_page
    
    # Save last section
    if current_section and content_buffer:
        current_section.content = '\n'.join(content_buffer).strip()
        if len(current_section.content) >= MIN_CHUNK_SIZE:
            sections.append(current_section)
    
    # Fallback Mechanism: If no sections found (no headers), chunk by length
    if not sections and md_text.strip():
        print("    ! No headers found. Using fallback length-based chunking.")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=MAX_CHUNK_SIZE,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(md_text)
        
        for i, chunk in enumerate(chunks):
            sections.append(MarkdownSection(
                level=1,
                title=f"Section {i+1} (Fallback)",
                content=chunk,
                start_page=1, # We lose page info in fallback for now, or could estimate
                end_page=1,
                parent_path="Fallback Content"
            ))
            
    return sections


def split_large_section(section: MarkdownSection) -> List[MarkdownSection]:
    """
    Split large sections into smaller chunks while preserving context
    """
    if len(section.content) <= MAX_CHUNK_SIZE:
        return [section]
    
    chunks = []
    paragraphs = section.content.split('\n\n')
    
    current_chunk_lines = []
    current_size = 0
    chunk_index = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        if current_size + para_size > MAX_CHUNK_SIZE and current_chunk_lines:
            # Save current chunk
            chunk_content = '\n\n'.join(current_chunk_lines)
            chunks.append(MarkdownSection(
                level=section.level,
                title=f"{section.title} (part {chunk_index + 1})",
                content=chunk_content,
                start_page=section.start_page,
                end_page=section.end_page,
                parent_path=section.parent_path
            ))
            
            current_chunk_lines = []
            current_size = 0
            chunk_index += 1
        
        current_chunk_lines.append(para)
        current_size += para_size
    
    # Save last chunk
    if current_chunk_lines:
        chunk_content = '\n\n'.join(current_chunk_lines)
        chunks.append(MarkdownSection(
            level=section.level,
            title=f"{section.title} (part {chunk_index + 1})" if chunk_index > 0 else section.title,
            content=chunk_content,
            start_page=section.start_page,
            end_page=section.end_page,
            parent_path=section.parent_path
        ))
    
    return chunks


def sections_to_documents(sections: List[MarkdownSection], source: str) -> List[Document]:
    """
    Convert MarkdownSection objects to LangChain Documents with enhanced metadata
    """
    documents = []
    
    for section in sections:
        # Enhanced metadata
        metadata = {
            "source": source,
            "section_path": section.section_path,
            "heading_level": section.level,
            "heading_title": section.title,
            "page_start": section.start_page,
            "page_end": section.end_page,
            "page": section.start_page,  # For compatibility with existing queries
            "chunk_method": "markdown_structure"
        }
        
        # Classify topic (same logic as existing code)
        content_lower = section.content.lower()
        if any(k in content_lower for k in ["패혈증", "sepsis", "젖산"]):
            metadata["topic"] = "sepsis"
        elif any(k in content_lower for k in ["승압", "vasopressor", "노르에피"]):
            metadata["topic"] = "pressor"
        elif any(k in content_lower for k in ["기계환기", "vent", "삽관"]):
            metadata["topic"] = "vent"
        
        doc = Document(
            page_content=section.content,
            metadata=metadata
        )
        documents.append(doc)
    
    return documents


def load_pdfs_as_markdown(pdf_folder: str, target_files: List[str] = None) -> List[Document]:
    """
    Load PDFs from folder, convert to markdown, and create structured documents.
    If target_files is provided, only process those files.
    """
    if not os.path.isdir(pdf_folder):
        raise FileNotFoundError(f"PDF folder not found: {pdf_folder}")
    
    pdf_paths = sorted(glob.glob(os.path.join(pdf_folder, "*.pdf")))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDFs found in: {pdf_folder}")
    
    # Filter if targets specified
    if target_files:
        pdf_paths = [p for p in pdf_paths if os.path.basename(p) in target_files]
        if not pdf_paths:
             print(f"Warning: None of the target files found in {pdf_folder}")
             return []

    all_documents = []
    print(f"[1] Converting {len(pdf_paths)} PDFs to Markdown...")
    
    for pdf_path in pdf_paths:
        print(f"\n  Processing: {os.path.basename(pdf_path)}")
        
        try:
            # Convert to markdown
            md_text, base_metadata = pdf_to_markdown(pdf_path)
            print(f"    ✓ Converted to markdown ({len(md_text):,} chars)")
            
            # Extract sections
            sections = extract_sections_from_markdown(md_text, base_metadata)
            print(f"    ✓ Extracted {len(sections)} sections")
            
            # Split large sections if needed
            final_sections = []
            for section in sections:
                final_sections.extend(split_large_section(section))
            
            if len(final_sections) > len(sections):
                print(f"    ✓ Split large sections: {len(sections)} → {len(final_sections)}")
            
            # Convert to documents
            docs = sections_to_documents(final_sections, base_metadata["source"])
            all_documents.extend(docs)
            print(f"    ✓ Created {len(docs)} document chunks")
            
        except Exception as e:
            print(f"    ✗ Error processing {os.path.basename(pdf_path)}: {e}")
            continue
    
    print(f"\n[1] Total documents created: {len(all_documents):,}")
    return all_documents


def build_vector_db():
    """
    # Build vector database with markdown-based chunking
    """
    # Target files that failed previously
    TARGET_FILES = [
        "2007 대한중환자의학회_만성기도폐쇄성질환 기계환기법 치료지침.pdf",
        "2022 대한심부전학회 심부전 진료지침.pdf",
        "2024 질병관리청 대한중환자의학회 성인 패혈증 초기치료지침서.pdf",
        "2024 질병관리청 성인 패혈증 초기치료지침서.pdf"
    ]
    
    # Load PDFs as structured markdown documents
    documents = load_pdfs_as_markdown(PDF_FOLDER, target_files=TARGET_FILES)
    
    if not documents:
        raise ValueError("No documents were created from PDFs")
    
    # Show sample
    print("\n[2] Sample Document Preview:")
    sample = documents[0]
    print(f"  Section Path: {sample.metadata.get('section_path', 'N/A')}")
    print(f"  Heading Level: {sample.metadata.get('heading_level', 'N/A')}")
    print(f"  Pages: {sample.metadata.get('page_start', 'N/A')}-{sample.metadata.get('page_end', 'N/A')}")
    print(f"  Content (first 300 chars):\n{sample.page_content[:300]}...")
    print("-" * 80)
    
    # Create embeddings
    print("\n[3] Creating embeddings and building vector store...")
    embeddings = HuggingFaceEmbeddings(
        model_name=LOCAL_EMBED_MODEL,
        model_kwargs={"device": "cpu"},  # Force CPU to avoid GPU memory issues
        encode_kwargs={"normalize_embeddings": True},
    )
    
    # Build vector store with batching for stability
    print(f"[3] Processing {len(documents)} documents in batches...")
    BATCH_SIZE = 10  # Process 10 documents at a time
    
    vectorstore = None
    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"    Processing batch {batch_num}/{total_batches} ({len(batch)} docs)...")
        
        if vectorstore is None:
            # Create initial vectorstore
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=PERSIST_DIR,
                collection_name=COLLECTION_NAME,
            )
        else:
            # Add to existing vectorstore
            vectorstore.add_documents(batch)
        
        print(f"    ✓ Batch {batch_num}/{total_batches} complete")
    
    print(f"\n[✓] Vector DB saved to: {PERSIST_DIR}")
    print(f"    Collection: {COLLECTION_NAME}")
    print(f"    Total chunks: {len(documents):,}")
    
    return vectorstore



if __name__ == "__main__":
    print("=" * 80)
    print("RAG Pipeline: PDF → Markdown → Structure-Aware Chunking")
    print("=" * 80)
    
    try:
        vectorstore = build_vector_db()
        print("\n✅ Success! Vector database created with markdown-based chunking.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
