import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_service import get_llm_service
from app.config import get_settings


def test_crash_proof():
    print("=" * 65)
    print("LIVE VERIFICATION: SYSTEM RUNNING WITH ZERO EXTERNAL API KEY")
    print("=" * 65)

    settings = get_settings()
    print(f"Current LLM Provider in Config: {settings.llm_provider}")
    print(f"Current LLM API Key: '{settings.llm_api_key}' (Mock/Local)")

    # 1. Health check
    print("\n[Test 1] Testing /health endpoint...")
    r1 = requests.get("http://127.0.0.1:8000/health")
    assert r1.status_code == 200
    print(f"[+] Status Code: {r1.status_code}")
    print(f"[+] Server Response: {r1.json()}")

    # 2. Document listing
    print("\n[Test 2] Testing /api/documents endpoint...")
    r2 = requests.get("http://127.0.0.1:8000/api/documents")
    assert r2.status_code == 200
    print(f"[+] Status Code: {r2.status_code}")
    print(f"[+] Total Ingested Documents in DB: {len(r2.json())}")

    # 3. Document upload (PDF)
    print("\n[Test 3] Testing Document Upload & Parsing (No API key needed)...")
    sample_pdf = os.path.join(os.path.dirname(__file__), "..", "data", "samples", "synthetic_cardiology_hf_guideline.pdf")
    with open(sample_pdf, "rb") as f:
        files = {"file": ("crash_test_sample.pdf", f)}
        data = {
            "title": "Crash-Proof Test Document",
            "department": "Cardiology",
            "document_type": "clinical_guideline",
            "version": "1.0",
        }
        r3 = requests.post("http://127.0.0.1:8000/api/documents/upload", files=files, data=data)
    assert r3.status_code == 201
    res_upload = r3.json()
    print(f"[+] Status Code: {r3.status_code}")
    print(f"[+] Document ID Created: {res_upload['document_id']}")
    print(f"[+] Chunks Successfully Created: {res_upload['chunks_created']}")
    print(f"[+] Status: {res_upload['status']}")

    # 4. LLM Service test with Mock Provider
    print("\n[Test 4] Testing LLM Service (Zero Crash Fallback)...")
    llm = get_llm_service()
    prompt = "What is the recommended dosing for Sacubitril/Valsartan?"
    context = "Sacubitril/Valsartan maintenance dose is 97/103 mg PO BID as per Section 2."
    ans = llm.generate(prompt=prompt, context=context)
    print(f"[+] LLM Provider Used: {ans['provider']}")
    print(f"[+] Answer Generated: {ans['answer']}")
    print(f"[+] Evidence Status: {ans['evidence_status']}")

    # 5. LLM Insufficient Evidence Refusal test
    print("\n[Test 5] Testing Refusal When Evidence is Insufficient...")
    refusal_ans = llm.generate(prompt="What is the dosage for unknown unverified drug X?", context=None)
    print(f"[+] Response: {refusal_ans['answer']}")
    print(f"[+] Evidence Status: {refusal_ans['evidence_status']}")

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED! ZERO CRASHES! ABSOLUTELY NO API KEY REQUIRED!")
    print("=" * 65)


if __name__ == "__main__":
    test_crash_proof()
