import os
import glob
import unicodedata
from typing import List

from langchain_community.document_loaders import PyMuPDFLoader  # ★ 한글 추출에 유리
from langchain_community.embeddings import HuggingFaceEmbeddings
# 대안: PDFPlumberLoader 도 있음 (필요 시 교체)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma


# 1) 로컬 임베딩 모델
LOCAL_EMBED_MODEL = "BAAI/bge-m3"

# 2) 경로/설정
PDF_FOLDER = "./guidelines"
PERSIST_DIR = "./db_medical"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def _clean_text(s: str) -> str:
    """PDF 추출 텍스트의 깨짐/제어문자/널문자 등을 완화"""
    if not s:
        return ""
    s = s.replace("\x00", " ")  # 널문자 제거(깨짐 원인)
    s = unicodedata.normalize("NFC", s)  # 한글 정규화
    return s


def load_pdfs_with_pymupdf(pdf_folder: str):
    if not os.path.isdir(pdf_folder):
        raise FileNotFoundError(f"PDF 폴더가 없습니다: {pdf_folder}")

    pdf_paths = sorted(glob.glob(os.path.join(pdf_folder, "*.pdf")))
    if not pdf_paths:
        raise FileNotFoundError(f"PDF가 없습니다: {pdf_folder}")

    docs = []
    print(f"[1] PDF 로드 시작: {len(pdf_paths)}개")

    for path in pdf_paths:
        loader = PyMuPDFLoader(path)
        loaded = loader.load()

        # page_content 클린
        for d in loaded:
            d.page_content = _clean_text(d.page_content)

        docs.extend(loaded)
        print(f" - {os.path.basename(path)}: pages={len(loaded)}")

    print(f"[1] 총 로드 페이지(Document): {len(docs)}")
    return docs


def build_vector_db():
    # A) 로드
    documents = load_pdfs_with_pymupdf(PDF_FOLDER)

    # B) 청킹
    print("[2] 텍스트 분할(Chunking)...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "•", "-", " ", ""],  # 가이드라인 문서에 유리
    )
    chunks = splitter.split_documents(documents)
    print(f"[2] chunk 수: {len(chunks):,}")

    # (선택) 한글 깨짐 검사용 샘플 출력
    sample = chunks[0].page_content[:300] if chunks else ""
    print("\n[샘플 chunk 미리보기(앞 300자)]")
    print(sample)
    print("--------------------------------------------------\n")

    # C) 임베딩 + Chroma 저장
    print("[3] 임베딩 + Chroma 인덱싱...")
    embeddings = HuggingFaceEmbeddings(
        model_name=LOCAL_EMBED_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name="medical_guidelines",
    )
    print(f"[완료] 벡터DB 저장 위치: {PERSIST_DIR}")
    return vectorstore


if __name__ == "__main__":
    build_vector_db()
