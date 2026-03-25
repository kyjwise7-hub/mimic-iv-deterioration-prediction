import os

from dotenv import load_dotenv
from openai import OpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# -------------------------
# 설정
# -------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env 또는 환경변수로 설정하세요.")
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

PERSIST_DIR = "./db_medical"
COLLECTION_NAME = "medical_guidelines"   # build할 때 썼다면 동일하게
HF_MODEL = "BAAI/bge-m3"                 # build할 때 썼다면 동일하게
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def load_vectorstore():
    """
    ✅ 중요:
    - Chroma를 persist_directory로 로드할 때도 embedding_function을 동일하게 지정하는 것이 안전합니다.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name=HF_MODEL,
        model_kwargs={"device": "cpu"},               # GPU 있으면 "cuda"
        encode_kwargs={"normalize_embeddings": True},
    )

    vectorstore = Chroma(
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )
    return vectorstore


def ask_question(vectorstore, query: str, k: int = 5):
    # ✅ 근거 표기용 템플릿 (source/page를 문맥 안에 포함시키는 방식)
    template = """당신은 의료 전문가(인턴, 레지던트)를 돕는 전문 어시스턴트입니다.
반드시 제공된 지침서 발췌(context)만 근거로 답변하세요.
지침서에 없는 내용은 추측하지 말고 "지침서에서 확인 불가"라고 답하세요.
답변에는 근거로 사용한 문서명(source)과 페이지(page)를 명시하세요.

[context]
{context}

[question]
{question}

[answer]
- 결론:
- 근거(문서/페이지):
- 추가 확인 필요:"""

    docs = vectorstore.similarity_search(query, k=k)
    context_blocks = []
    for doc in docs:
        meta = doc.metadata or {}
        src = meta.get("source", "unknown_source")
        page = meta.get("page", meta.get("page_number", "unknown_page"))
        src_name = os.path.basename(src) if isinstance(src, str) else str(src)
        content = (doc.page_content or "").strip()
        context_blocks.append(
            f"[source] {src_name}\n[page] {page}\n[content]\n{content}"
        )
    context = "\n\n".join(context_blocks)
    prompt = template.format(context=context, question=query)

    print(f"\n질문: {query}")
    response = OPENAI_CLIENT.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a medical assistant that only answers from provided context."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    answer = response.choices[0].message.content or ""

    print("\n답변:")
    print(answer)

    # ✅ 근거 문서/페이지를 “확실히” 출력 (모델이 누락해도 여기서 보강 가능)
    print("\n[검색 근거 Top 문서]")
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata or {}
        src = meta.get("source", "unknown_source")
        page = meta.get("page", meta.get("page_number", "unknown_page"))
        # 파일명만 보기 좋게
        src_name = os.path.basename(src) if isinstance(src, str) else str(src)
        snippet = (doc.page_content or "").replace("\n", " ")[:180]
        print(f"{i}. {src_name} / page={page} :: {snippet}...")


if __name__ == "__main__":
    # ✅ 1) DB 로드 (이미 구축된 db_medical 사용)
    db = load_vectorstore()

    # ✅ 2) 질문
    ask_question(db, "패혈증 환자의 초기 수액 소생술 권고 사항은?", k=5)
