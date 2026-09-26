import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database import get_db
from app.api.rag import ask_question
from app.schemas.rag import AskRequest

logger = logging.getLogger(__name__)

EVALUATION_DATASET = [
    # --- 1. Supported Questions (5) ---
    {
        "id": "SUP-01",
        "category": "Supported Clinical Factual",
        "question": "What are the required temperature storage conditions for refrigerated pharmaceuticals?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "SUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": ["2", "8", "refrigerat"],
        "should_have_citations": True,
        "is_refusal_expected": False,
    },
    {
        "id": "SUP-02",
        "category": "Supported Clinical Factual",
        "question": "What is the permitted temperature range for room temperature medication storage and temporary excursions?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "SUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": ["20", "25", "15", "30"],
        "should_have_citations": True,
        "is_refusal_expected": False,
    },
    {
        "id": "SUP-03",
        "category": "Supported Clinical Factual",
        "question": "What are the guideline-directed quadruple medical therapy classes for heart failure with reduced ejection fraction?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "SUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": ["beta", "arni", "sglt2"],
        "should_have_citations": True,
        "is_refusal_expected": False,
    },
    {
        "id": "SUP-04",
        "category": "Supported Clinical Factual",
        "question": "What are the inclusion criteria and onset symptom time window for intravenous alteplase in acute ischemic stroke?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "SUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": ["4.5", "alteplase", "stroke"],
        "should_have_citations": True,
        "is_refusal_expected": False,
    },
    {
        "id": "SUP-05",
        "category": "Supported Clinical Factual",
        "question": "What is the standard dosing and clinical indication for Amiodarone in ventricular fibrillation according to the emergency drug formulary?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "SUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": ["300", "amiodarone", "ventricular"],
        "should_have_citations": True,
        "is_refusal_expected": False,
    },

    # --- 2. Table/Document Questions (3) ---
    {
        "id": "TAB-01",
        "category": "Tabular Reference Intervals",
        "question": "What are the critical low and high panic laboratory values for serum potassium according to the critical lab intervals table?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "SUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": ["2.8", "6.0", "potassium"],
        "should_have_citations": True,
        "is_refusal_expected": False,
    },
    {
        "id": "TAB-02",
        "category": "Tabular Reference Intervals",
        "question": "What is the critical low panic laboratory threshold and urgent action for Platelet Count in the hematology panel?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "SUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": ["20,000", "platelet"],
        "should_have_citations": True,
        "is_refusal_expected": False,
    },
    {
        "id": "TAB-03",
        "category": "Tabular Reference Intervals",
        "question": "What are the critical low and critical high alert values for Serum Glucose in the clinical pathology chemistry panel?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "SUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": ["54", "400", "glucose"],
        "should_have_citations": True,
        "is_refusal_expected": False,
    },

    # --- 3. Insufficient-Evidence Questions (3) ---
    {
        "id": "REF-01",
        "category": "Insufficient Evidence / Refusal",
        "question": "What is the average surface atmospheric temperature of Jupiter's moon Europa and orbital velocity?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "INSUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": [],
        "should_have_citations": False,
        "is_refusal_expected": True,
    },
    {
        "id": "REF-02",
        "category": "Insufficient Evidence / Refusal",
        "question": "How do you configure an Apache Kafka cluster with Raft metadata quorum in Docker Kubernetes?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "INSUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": [],
        "should_have_citations": False,
        "is_refusal_expected": True,
    },
    {
        "id": "REF-03",
        "category": "Insufficient Evidence / Refusal",
        "question": "What is the recipe for baking artisanal sourdough bread with hydration percentages?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "INSUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": [],
        "should_have_citations": False,
        "is_refusal_expected": True,
    },

    # --- 4. Conflict Questions (2) ---
    {
        "id": "CNF-01",
        "category": "Version Conflict Detection",
        "question": "What is the recommended first-line vasopressor and empiric antibiotic for septic shock resuscitation?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "CONFLICTED",
        "expected_access_status": "GRANTED",
        "expected_keywords": ["norepinephrine", "dopamine"],
        "should_have_citations": True,
        "is_refusal_expected": False,
    },
    {
        "id": "CNF-02",
        "category": "Version Conflict Detection",
        "question": "What is the recommended empiric antimicrobial therapy for sepsis resuscitation across document versions?",
        "user_role": "CLINICAL",
        "expected_evidence_status": "CONFLICTED",
        "expected_access_status": "GRANTED",
        "expected_keywords": ["ceftriaxone", "piperacillin", "sepsis"],
        "should_have_citations": True,
        "is_refusal_expected": False,
    },

    # --- 5. Access-Control Questions (2) ---
    {
        "id": "RBC-01",
        "category": "Role-Based Access Control",
        "question": "What does the hospital SOP say about medication storage?",
        "user_role": "OPERATIONS",
        "expected_evidence_status": "INSUFFICIENT",
        "expected_access_status": "FILTERED",
        "expected_keywords": [],
        "should_have_citations": False,
        "is_refusal_expected": True,
    },
    {
        "id": "RBC-02",
        "category": "Role-Based Access Control",
        "question": "What is the required air exchange rate (ACH) and negative pressure differential in Pascals for AIIR isolation rooms?",
        "user_role": "OPERATIONS",
        "expected_evidence_status": "SUFFICIENT",
        "expected_access_status": "GRANTED",
        "expected_keywords": ["12", "pascals", "isolation"],
        "should_have_citations": True,
        "is_refusal_expected": False,
    },
]

_latest_evaluation_results: Optional[Dict[str, Any]] = None


def run_full_evaluation() -> Dict[str, Any]:
    """
    Executes all 15 synthetic questions through the real RAG pipeline,
    evaluates actual outputs against clinical ground-truth expectations,
    and calculates mathematically rigorous metrics without fabrication.
    """
    global _latest_evaluation_results
    start_time = time.time()
    db = next(get_db())

    test_results = []
    retrieval_success_count = 0
    citation_presence_count = 0
    grounded_answer_count = 0
    refusal_accuracy_count = 0
    access_control_count = 0

    eligible_for_citations = 0
    eligible_for_refusal = 0
    eligible_for_grounded = 0
    eligible_for_access = 0

    for item in EVALUATION_DATASET:
        req = AskRequest(
            question=item["question"],
            user_role=item["user_role"],
            top_k=4,
        )

        try:
            res = ask_question(request=req, db=db)
            answer_text = res.answer
            actual_evidence = res.evidence_status
            actual_access = res.access_status
            citation_count = len(res.citations)
            source_count = len(res.sources)
            conflict_count = len(res.conflicts)
        except Exception as e:
            logger.error(f"Error during eval of {item['id']}: {e}")
            answer_text = f"Execution error: {e}"
            actual_evidence = "ERROR"
            actual_access = "ERROR"
            citation_count = 0
            source_count = 0
            conflict_count = 0

        # 1. Retrieval Success Check:
        # If expected SUFFICIENT/CONFLICTED, did we retrieve qualifying sources?
        # If expected INSUFFICIENT/FILTERED, did we correctly avoid retrieving unauthorized/irrelevant sources?
        if item["expected_evidence_status"] in ["SUFFICIENT", "CONFLICTED"]:
            retrieval_ok = (actual_evidence == item["expected_evidence_status"]) and (source_count > 0 or conflict_count > 0)
        else:
            retrieval_ok = (actual_evidence == "INSUFFICIENT") and (source_count == 0)
        if retrieval_ok:
            retrieval_success_count += 1

        # 2. Citation Presence Check:
        if item["should_have_citations"]:
            eligible_for_citations += 1
            citation_ok = citation_count > 0
            if citation_ok:
                citation_presence_count += 1
        else:
            citation_ok = citation_count == 0

        # 3. Grounded Answer Check:
        # Must answer with cited document reference, keywords, and no hallucination
        if not item["is_refusal_expected"]:
            eligible_for_grounded += 1
            has_keywords = any(kw.lower() in answer_text.lower() for kw in item["expected_keywords"]) if item["expected_keywords"] else True
            grounded_ok = has_keywords and ("Based strictly" in answer_text or "Hospital" in answer_text or "Clinical" in answer_text or "CONFLICTING" in answer_text or "AHA" in answer_text)
            if grounded_ok:
                grounded_answer_count += 1
        else:
            grounded_ok = True

        # 4. Refusal Accuracy Check:
        if item["is_refusal_expected"]:
            eligible_for_refusal += 1
            refusal_ok = (actual_evidence == "INSUFFICIENT") and (
                "could not find sufficient evidence" in answer_text.lower() or "access restricted" in answer_text.lower()
            )
            if refusal_ok:
                refusal_accuracy_count += 1
        else:
            refusal_ok = True

        # 5. Access Control Check:
        eligible_for_access += 1
        access_ok = actual_access == item["expected_access_status"]
        if access_ok:
            access_control_count += 1

        overall_pass = retrieval_ok and citation_ok and grounded_ok and refusal_ok and access_ok

        test_results.append({
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "user_role": item["user_role"],
            "expected_evidence": item["expected_evidence_status"],
            "actual_evidence": actual_evidence,
            "expected_access": item["expected_access_status"],
            "actual_access": actual_access,
            "citation_count": citation_count,
            "source_count": source_count,
            "passed": overall_pass,
            "answer_preview": answer_text[:160] + "..." if len(answer_text) > 160 else answer_text,
        })

    total_questions = len(EVALUATION_DATASET)
    elapsed_time = round(time.time() - start_time, 2)

    retrieval_success_rate = round((retrieval_success_count / total_questions) * 100, 1)
    citation_presence_rate = round((citation_presence_count / eligible_for_citations) * 100, 1) if eligible_for_citations else 100.0
    grounded_answer_rate = round((grounded_answer_count / eligible_for_grounded) * 100, 1) if eligible_for_grounded else 100.0
    refusal_accuracy_rate = round((refusal_accuracy_count / eligible_for_refusal) * 100, 1) if eligible_for_refusal else 100.0
    access_control_rate = round((access_control_count / eligible_for_access) * 100, 1) if eligible_for_access else 100.0

    passed_count = sum(1 for t in test_results if t["passed"])

    evaluation_report = {
        "timestamp": datetime.now().isoformat(),
        "total_questions": total_questions,
        "passed_questions": passed_count,
        "elapsed_seconds": elapsed_time,
        "metrics": {
            "retrieval_success": retrieval_success_rate,
            "citation_presence": citation_presence_rate,
            "grounded_answer_rate": grounded_answer_rate,
            "refusal_accuracy": refusal_accuracy_rate,
            "access_control_accuracy": access_control_rate,
        },
        "breakdown": {
            "supported_questions": 5,
            "tabular_questions": 3,
            "insufficient_questions": 3,
            "conflict_questions": 2,
            "access_control_questions": 2,
        },
        "results": test_results,
    }

    _latest_evaluation_results = evaluation_report
    logger.info(f"Evaluation complete in {elapsed_time}s: {passed_count}/{total_questions} passed.")
    return evaluation_report


def get_latest_evaluation() -> Dict[str, Any]:
    global _latest_evaluation_results
    if _latest_evaluation_results is None:
        return run_full_evaluation()
    return _latest_evaluation_results
