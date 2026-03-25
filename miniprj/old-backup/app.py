import json
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI

from rule_engine import create_engine
from clinical_summary import create_clinical_summary_generator
from gentle_report import create_gentle_report_generator
from qa_interface import create_qa_interface

load_dotenv()

PERSIST_DIR = os.getenv("PERSIST_DIR", "./db_medical")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "medical_guidelines")
HF_MODEL = os.getenv("HF_MODEL", "BAAI/bge-m3")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

app = Flask(__name__)


OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Initialize rule engine
RULE_ENGINE = create_engine(protocols_dir="./protocols")

# Initialize LLM modules
try:
    CLINICAL_SUMMARY_GENERATOR = create_clinical_summary_generator()
    GENTLE_REPORT_GENERATOR = create_gentle_report_generator()
    QA_INTERFACE = create_qa_interface()
    print("✅ LLM modules initialized successfully")
except Exception as e:
    print(f"⚠️  LLM modules initialization failed: {e}")
    CLINICAL_SUMMARY_GENERATOR = None
    GENTLE_REPORT_GENERATOR = None
    QA_INTERFACE = None



def classify_intent(q: str) -> str:
    ql = q.lower()
    if any(k in ql for k in ["패혈증", "sepsis", "젖산", "lactate"]):
        return "sepsis"
    if any(k in ql for k in ["승압", "바소", "vasopressor", "norepi", "노르에피", "map"]):
        return "pressor"
    if any(k in ql for k in ["기계환기", "vent", "삽관", "intub", "hfnc", "niv"]):
        return "vent"
    if any(k in ql for k in ["rrt", "icu call", "에스컬", "escalation", "중환자실"]):
        return "icu_escalation"
    return "general"


SEPSIS_STEP_QUERIES = {
    "즉시(0–15분)": [
        "패혈증 초기 번들 lactate 측정 재측정",
        "패혈증 blood culture 항생제 투여 1시간",
    ],
    "수액 소생": [
        "패혈증 30 ml/kg crystalloid 3시간",
    ],
    "승압제": [
        "패혈증 MAP 65 norepinephrine 승압제",
    ],
    "Escalation": [
        "패혈증 지속 저혈압 젖산 상승 ICU escalation RRT",
    ],
}


def build_protocol_with_llm(query: str, intent: str, evidence: list):
    if OPENAI_CLIENT is None:
        return None

    if not evidence:
        return {
            "intent": intent,
            "protocol": {
                "title": f"{intent} 프로토콜",
                "steps": [{"order": 1, "label": "요약", "actions": ["근거 부족"], "evidence_ids": []}],
                "disclaimer": "환자 상태에 따라 조정 필요",
            },
            "used_evidence_ids": [],
        }

    ctx = []
    allowed_ids = []
    for e in evidence:
        meta = e["meta"]
        allowed_ids.append(e["evidence_id"])
        ctx.append(
            {
                "evidence_id": e["evidence_id"],
                "source": meta.get("source"),
                "page": meta.get("page"),
                "text": (e["content"] or "")[:1800],
                "step_hint": e.get("step_hint"),
            }
        )

    system = (
        "당신은 ICU 임상 지원 도우미입니다. "
        "반드시 제공된 EVIDENCE에 근거한 내용만 말하세요. "
        "각 action 끝에 evidence_id를 최소 1개 이상 인용하세요. "
        "각 step의 actions는 비어있으면 안 됩니다. "
        "근거가 없으면 action 1개를 "
        "\"근거 부족: 추가 데이터/추가 문서 필요\"로 채우고 evidence_ids는 비워두세요. "
        "근거가 없으면 '근거 부족'이라고 쓰고 임의로 만들지 마세요. "
        "출력은 반드시 JSON만 반환하세요."
    )

    if intent == "sepsis":
        template = {
            "title": "패혈증 초기 대응 (성인, ICU)",
            "steps": [
                {"order": 1, "label": "즉시(0–15분)", "actions": [], "evidence_ids": []},
                {"order": 2, "label": "수액 소생", "actions": [], "evidence_ids": []},
                {"order": 3, "label": "승압제", "actions": [], "evidence_ids": []},
                {"order": 4, "label": "Escalation", "actions": [], "evidence_ids": []},
            ],
            "disclaimer": "환자 상태에 따라 조정 필요",
        }
    else:
        template = {
            "title": f"{intent} 프로토콜",
            "steps": [{"order": 1, "label": "요약", "actions": [], "evidence_ids": []}],
            "disclaimer": "환자 상태에 따라 조정 필요",
        }

    user = {
        "query": query,
        "intent": intent,
        "protocol_template": template,
        "EVIDENCE": ctx,
        "ALLOWED_EVIDENCE_IDS": allowed_ids,
        "output_schema": {
            "intent": "string",
            "protocol": "object(title, steps[], disclaimer)",
            "used_evidence_ids": "array of evidence_id used",
        },
    }

    resp = OPENAI_CLIENT.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(resp.choices[0].message.content)


def _load_vectorstore() -> Chroma:
    embeddings = HuggingFaceEmbeddings(
        model_name=HF_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return Chroma(
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )


VECTORSTORE = _load_vectorstore()


def retrieve_evidence(vectorstore: Chroma, query: str, topic: str, k: int = 8):
    where = None
    if topic != "general":
        where = {"topic": topic}

    query_embedding = vectorstore._embedding_function.embed_query(query)
    res = vectorstore._collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    if (not res.get("documents") or not res["documents"][0]) and topic != "general":
        res = vectorstore._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=None,
            include=["documents", "metadatas", "distances"],
        )

    docs = res["documents"][0]
    metas = res["metadatas"][0]
    ids = res["ids"][0]
    dists = res["distances"][0]

    evidence = []
    for _id, doc, meta, dist in zip(ids, docs, metas, dists):
        evidence.append(
            {
                "evidence_id": _id,
                "content": doc,
                "meta": meta or {},
                "score": float(1.0 - dist),
            }
        )
    return evidence


def retrieve_evidence_multi(vectorstore: Chroma, intent: str, user_query: str, k_each: int = 4):
    evidence_all = []
    if intent == "sepsis":
        for step, qs in SEPSIS_STEP_QUERIES.items():
            for q in qs:
                ev = retrieve_evidence(vectorstore, q, topic=intent, k=k_each)
                for e in ev:
                    e["step_hint"] = step
                evidence_all.extend(ev)
    else:
        evidence_all = retrieve_evidence(vectorstore, user_query, topic=intent, k=12)

    evidence_all = dedup_evidence(evidence_all)
    return evidence_all


def dedup_evidence(evidence):
    seen = set()
    out = []
    for e in sorted(evidence, key=lambda x: x["score"], reverse=True):
        key = (e["meta"].get("source"), e["meta"].get("page"))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def sanitize_protocol_evidence_ids(protocol: dict, allowed_ids: set):
    if not protocol or "steps" not in protocol:
        return
    for step in protocol.get("steps", []):
        ids = step.get("evidence_ids", [])
        step["evidence_ids"] = [i for i in ids if i in allowed_ids]


def package_evidence_for_ui(evidence: list, used_ids: set):
    out = []
    for e in evidence:
        if e["evidence_id"] not in used_ids:
            continue
        meta = e["meta"]
        content = e["content"] or ""
        snippet = content[:400] + "…" if len(content) > 400 else content
        out.append(
            {
                "id": e["evidence_id"],
                "doc_title": meta.get("source"),
                "page": meta.get("page"),
                "snippet": snippet,
            }
        )
    return out


def normalize_protocol_for_ui(protocol: dict):
    if not protocol:
        return {"title": "", "steps": [], "disclaimer": ""}
    steps = []
    for step in protocol.get("steps", []):
        steps.append(
            {
                "order": step.get("order"),
                "title": step.get("label", ""),
                "actions": step.get("actions", []),
            }
        )
    return {
        "title": protocol.get("title", ""),
        "steps": steps,
        "disclaimer": protocol.get("disclaimer", ""),
    }


@app.post("/search")
def search():
    payload = request.get_json(force=True)
    query = (payload.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400

    intent = classify_intent(query)
    evidence = retrieve_evidence_multi(VECTORSTORE, intent, query, k_each=4)

    results = []
    for e in evidence:
        meta = e["meta"]
        src = meta.get("source", "unknown_source")
        page = meta.get("page", meta.get("page_number", "unknown_page"))
        results.append(
            {
                "evidence_id": e["evidence_id"],
                "source": src,
                "page": page,
                "score": e["score"],
                "content": e["content"],
            }
        )

    return jsonify({"intent": intent, "results": results})


@app.post("/protocol")
def protocol():
    payload = request.get_json(force=True)
    query = (payload.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400

    intent = classify_intent(query)
    evidence = retrieve_evidence_multi(VECTORSTORE, intent, query, k_each=4)

    llm_out = build_protocol_with_llm(query, intent, evidence) or {}
    allowed_ids = {e["evidence_id"] for e in evidence}
    used_ids = set(llm_out.get("used_evidence_ids", [])) & allowed_ids
    sanitize_protocol_evidence_ids(llm_out.get("protocol"), allowed_ids)
    evidence_ui = package_evidence_for_ui(evidence, used_ids)

    response = {
        "intent": llm_out.get("intent", intent),
        "protocol": normalize_protocol_for_ui(llm_out.get("protocol", {})),
        "evidence": evidence_ui,
    }
    return jsonify(response)


@app.post("/api/evaluate-protocols")
def evaluate_protocols():
    """
    Evaluate rule-based protocols against patient features
    
    Input JSON:
    {
      "patient_id": "demo_001",  # optional
      "map": 58,
      "sbp": 82,
      "lactate": 4.2,
      "spo2": 89,
      "fio2": 0.5,
      "rr": 32,
      "on_oxygen": true,
      "on_hfnc": false,
      "on_vent": false,
      "on_pressor": false,
      "urine_output_ml_per_kg_hr": 0.3
    }
    
    Output JSON:
    {
      "patient_id": "demo_001",
      "active_protocols": ["sepsis", "pressor", "vent"],
      "actions": [
        {
          "protocol": "sepsis",
          "priority": "STAT",
          "action": "Crystalloid 30 mL/kg, 3시간 내 투여 고려",
          "evidence": {
            "source": "KCDC + KSCCM 2024",
            "page": 45
          }
        },
        ...
      ]
    }
    """
    payload = request.get_json(force=True)
    
    # Validate required fields
    if not payload:
        return jsonify({"error": "Patient features are required"}), 400
    
    # Evaluate protocols using rule engine
    try:
        result = RULE_ENGINE.evaluate_all_protocols(payload)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Protocol evaluation failed: {str(e)}"}), 500



@app.route("/protocol-ui", methods=["GET", "POST"])
def protocol_ui():
    query = ""
    intent = "general"
    protocol = None
    evidence = []
    if request.method == "POST":
        query = (request.form.get("query") or "").strip()
        if query:
            intent = classify_intent(query)
            evidence_all = retrieve_evidence_multi(VECTORSTORE, intent, query, k_each=4)
            llm_out = build_protocol_with_llm(query, intent, evidence_all) or {}
            allowed_ids = {e["evidence_id"] for e in evidence_all}
            sanitize_protocol_evidence_ids(llm_out.get("protocol"), allowed_ids)
            used_ids = set(llm_out.get("used_evidence_ids", [])) & allowed_ids
            evidence = package_evidence_for_ui(evidence_all, used_ids)
            protocol = normalize_protocol_for_ui(llm_out.get("protocol", {}))
    return render_template(
        "protocol.html",
        query=query,
        intent=intent,
        protocol=protocol,
        evidence=evidence,
    )


@app.route("/", methods=["GET"])
def index():
    """
    Main dashboard with tabbed UI for testing LLM modules
    """
    return render_template("llm_dashboard.html")


@app.route("/old-index", methods=["GET", "POST"])
def old_index():
    """
    Original index page (preserved for reference)
    """
    query = ""
    results = []
    intent = "general"
    protocol = None
    if request.method == "POST":
        query = (request.form.get("query") or "").strip()
        if query:
            intent = classify_intent(query)
            evidence = retrieve_evidence_multi(VECTORSTORE, intent, query, k_each=4)
            for e in evidence:
                meta = e["meta"]
                src = meta.get("source", "unknown_source")
                page = meta.get("page", meta.get("page_number", "unknown_page"))
                src_name = os.path.basename(src) if isinstance(src, str) else str(src)
                snippet = (e["content"] or "").replace("\n", " ").strip()
                results.append(
                    {
                        "source": src_name,
                        "page": page,
                        "snippet": snippet[:300],
                        "score": f"{e['score']:.3f}",
                    }
                )
            protocol = build_protocol_with_llm(query, intent, evidence)
            if protocol:
                allowed_ids = {e["evidence_id"] for e in evidence}
                sanitize_protocol_evidence_ids(protocol.get("protocol"), allowed_ids)
    return render_template(
        "index.html",
        query=query,
        results=results,
        intent=intent,
        protocol=protocol,
    )


@app.route("/protocol-cards")
def protocol_cards():
    """
    Render the rule-based protocol evaluation UI
    """
    return render_template("protocol_cards.html")


# ============================================================
# New LLM Feature Endpoints
# ============================================================


@app.post("/api/clinical-summary")
def clinical_summary_endpoint():
    """
    Generate clinical summary for medical staff
    
    Input JSON:
    {
      "patient_id": "demo_001",
      "vitals": {"map": 58, "sbp": 82, "hr": 120},
      "labs": {"lactate": 4.2, "wbc": 18},
      "shap_features": [
        {"feature": "map_mean", "value": 58, "contribution": -0.35},
        {"feature": "lactate_last", "value": 4.2, "contribution": 0.28}
      ],
      "prediction_risk": {"mortality": 0.75, "pressor": 0.85, "vent": 0.45},
      "data_quality_flags": ["MAP 센서 간헐적 결측"]
    }
    
    Output JSON:
    {
      "patient_id": "demo_001",
      "risk_level": "high",
      "risk_score": 0.85,
      "summary": "...",
      "key_features": [...],
      "recommended_actions": [...],
      "data_quality_alerts": [...],
      "timestamp": "2026-01-02T11:46:00"
    }
    """
    if not CLINICAL_SUMMARY_GENERATOR:
        return (
            jsonify({"error": "Clinical summary service is not available"}),
            503,
        )

    payload = request.get_json(force=True)

    # Validate required fields
    required = ["patient_id", "vitals", "labs", "shap_features", "prediction_risk"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        summary = CLINICAL_SUMMARY_GENERATOR.generate_summary(
            patient_id=payload["patient_id"],
            vitals=payload["vitals"],
            labs=payload["labs"],
            shap_features=payload["shap_features"],
            prediction_risk=payload["prediction_risk"],
            data_quality_flags=payload.get("data_quality_flags"),
        )

        # Add server timestamp
        summary["timestamp"] = datetime.now().isoformat()

        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": f"Clinical summary generation failed: {str(e)}"}), 500


@app.post("/api/gentle-report")
def gentle_report_endpoint():
    """
    Generate gentle report for patient family (requires medical staff approval)
    
    Input JSON:
    {
      "patient_id": "demo_001",
      "approved_by": "Dr. Kim",  # Required!
      "clinical_summary": {
        "risk_level": "high",
        "summary": "...",
        "key_features": [...]
      }
    }
    
    Output JSON:
    {
      "patient_id": "demo_001",
      "status": "불안정",
      "simple_explanation": "...",
      "what_to_expect": "...",
      "family_guidance": "...",
      "approved_by": "Dr. Kim",
      "approved": true,
      "timestamp": "2026-01-02T11:46:00"
    }
    """
    if not GENTLE_REPORT_GENERATOR:
        return (
            jsonify({"error": "Gentle report service is not available"}),
            503,
        )

    payload = request.get_json(force=True)

    # Validate required fields
    if "patient_id" not in payload:
        return jsonify({"error": "Missing required field: patient_id"}), 400

    if "clinical_summary" not in payload:
        return jsonify({"error": "Missing required field: clinical_summary"}), 400

    try:
        report = GENTLE_REPORT_GENERATOR.generate_from_clinical_summary(
            clinical_summary_output=payload["clinical_summary"],
            approved_by=payload.get("approved_by"),
            require_approval=True,
        )

        # Add server timestamp
        report["timestamp"] = datetime.now().isoformat()

        return jsonify(report)
    except Exception as e:
        return jsonify({"error": f"Gentle report generation failed: {str(e)}"}), 500


@app.post("/api/query")
def query_endpoint():
    """
    Parse natural language query and return filter parameters
    
    Input JSON:
    {
      "query": "최근 2시간 내 위험도 급상승한 환자 보여줘"
    }
    
    Output JSON:
    {
      "filters": {"time_range": "2h", "risk_change": "급상승"},
      "interpretation": "최근 2시간 동안 위험도가 급격히 상승한 환자를 조회합니다.",
      "sort_by": "risk_change_rate",
      "original_query": "..."
    }
    """
    if not QA_INTERFACE:
        return (
            jsonify({"error": "Q&A interface service is not available"}),
            503,
        )

    payload = request.get_json(force=True)

    # Validate required field
    if "query" not in payload or not payload["query"].strip():
        return jsonify({"error": "Missing or empty query"}), 400

    try:
        result = QA_INTERFACE.parse_query(payload["query"])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Query parsing failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5003)
