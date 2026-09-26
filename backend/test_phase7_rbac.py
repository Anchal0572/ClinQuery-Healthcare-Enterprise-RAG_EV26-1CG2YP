import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"


def test_rbac_scenarios():
    print("=" * 70)
    print("  PHASE 7 RBAC TEST: Role-Based Pre-Retrieval Access Control")
    print("=" * 70)

    # ---------------------------------------------------------
    # TEST 1: Clinical user querying clinical document
    # ---------------------------------------------------------
    print("\n[TEST 1] Clinical user querying restricted clinical document (Medication Storage SOP)...")
    payload1 = {
        "question": "What does the hospital SOP say about medication storage?",
        "user_role": "CLINICAL",
        "user_id": 1,
    }
    req1 = urllib.request.Request(
        f"{BASE_URL}/api/rag/ask",
        data=json.dumps(payload1).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    res1 = json.loads(urllib.request.urlopen(req1).read().decode("utf-8"))

    print(f"  User Role:       {res1.get('user_role')}")
    print(f"  Access Status:   {res1.get('access_status')}")
    print(f"  Evidence Status: {res1.get('evidence_status')}")
    print(f"  Citations Count: {len(res1.get('citations', []))}")
    print(f"  Sources Count:   {len(res1.get('sources', []))}")
    print(f"  Answer Preview:  {res1.get('answer', '')[:110]}...")

    assert res1.get("access_status") == "GRANTED", f"Expected GRANTED, got {res1.get('access_status')}"
    assert res1.get("evidence_status") == "SUFFICIENT", f"Expected SUFFICIENT, got {res1.get('evidence_status')}"
    assert len(res1.get("citations", [])) > 0, "Expected citations for clinical user"
    print("  --> PASS: Clinical user successfully accessed clinical document.")

    # ---------------------------------------------------------
    # TEST 2: Operations user querying restricted clinical document
    # ---------------------------------------------------------
    print("\n[TEST 2] Operations user querying restricted clinical document (Medication Storage SOP)...")
    payload2 = {
        "question": "What does the hospital SOP say about medication storage?",
        "user_role": "OPERATIONS",
        "user_id": 2,
    }
    req2 = urllib.request.Request(
        f"{BASE_URL}/api/rag/ask",
        data=json.dumps(payload2).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    res2 = json.loads(urllib.request.urlopen(req2).read().decode("utf-8"))

    print(f"  User Role:       {res2.get('user_role')}")
    print(f"  Access Status:   {res2.get('access_status')}")
    print(f"  Evidence Status: {res2.get('evidence_status')}")
    print(f"  Citations Count: {len(res2.get('citations', []))}")
    print(f"  Sources Count:   {len(res2.get('sources', []))}")
    print(f"  Answer:          {res2.get('answer')}")

    assert res2.get("access_status") == "FILTERED", f"Expected FILTERED, got {res2.get('access_status')}"
    assert len(res2.get("citations", [])) == 0, "Unauthorized citations must be empty!"
    assert len(res2.get("sources", [])) == 0, "Unauthorized sources must never enter context!"
    assert "refrigerated" not in res2.get("answer", "").lower(), "Must NOT leak restricted content!"
    assert "medication" not in res2.get("answer", "").lower() or "access restricted" in res2.get("answer", "").lower(), "Answer must be restricted refusal"
    print("  --> PASS: Operations user was blocked! Zero clinical chunks entered context or citations.")

    # ---------------------------------------------------------
    # TEST 3: Operations user querying operations document
    # ---------------------------------------------------------
    print("\n[TEST 3] Operations user querying operations document (Biohazard & HVAC SOP)...")
    payload3 = {
        "question": "What is the requirement for biohazard waste containers and isolation room air changes?",
        "user_role": "OPERATIONS",
        "user_id": 2,
    }
    req3 = urllib.request.Request(
        f"{BASE_URL}/api/rag/ask",
        data=json.dumps(payload3).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    res3 = json.loads(urllib.request.urlopen(req3).read().decode("utf-8"))

    print(f"  User Role:       {res3.get('user_role')}")
    print(f"  Access Status:   {res3.get('access_status')}")
    print(f"  Evidence Status: {res3.get('evidence_status')}")
    print(f"  Citations Count: {len(res3.get('citations', []))}")
    print(f"  Sources Count:   {len(res3.get('sources', []))}")
    print(f"  Answer Preview:  {res3.get('answer', '')[:120]}...")

    assert res3.get("access_status") == "GRANTED", f"Expected GRANTED, got {res3.get('access_status')}"
    assert len(res3.get("citations", [])) > 0, "Operations user should have citations for operations doc"
    print("  --> PASS: Operations user successfully accessed allowed operations document.")

    # ---------------------------------------------------------
    # TEST 4: Clinical user querying operations-only document
    # ---------------------------------------------------------
    print("\n[TEST 4] Clinical user querying operations-only document (AIIR Isolation HVAC SOP)...")
    payload4 = {
        "question": "What is the required air exchange rate (ACH) and negative pressure differential in Pascals for AIIR isolation rooms?",
        "user_role": "CLINICAL",
        "user_id": 1,
    }
    req4 = urllib.request.Request(
        f"{BASE_URL}/api/rag/ask",
        data=json.dumps(payload4).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    res4 = json.loads(urllib.request.urlopen(req4).read().decode("utf-8"))

    print(f"  User Role:       {res4.get('user_role')}")
    print(f"  Access Status:   {res4.get('access_status')}")
    print(f"  Evidence Status: {res4.get('evidence_status')}")
    print(f"  Citations Count: {len(res4.get('citations', []))}")
    print(f"  Answer:          {res4.get('answer')}")

    assert res4.get("access_status") == "FILTERED", f"Expected FILTERED, got {res4.get('access_status')}"
    assert len(res4.get("citations", [])) == 0, "Citations must be empty for unauthorized doc"
    print("  --> PASS: Clinical user restricted from operations-only document.")

    # ---------------------------------------------------------
    # TEST 5: Verify Audit Logs record access status and user role
    # ---------------------------------------------------------
    print("\n[TEST 5] Checking Audit Logs endpoint (/api/audit-logs)...")
    req_logs = urllib.request.Request(f"{BASE_URL}/api/audit-logs?limit=5")
    logs = json.loads(urllib.request.urlopen(req_logs).read().decode("utf-8"))

    print(f"  Recent Audit Logs retrieved: {len(logs)}")
    for l in logs[:4]:
        print(f"  - Log #{l['id']} | Role: {l.get('user_role')} | Access: {l.get('access_status')} | Evidence: {l.get('evidence_status')}")
        print(f"    Q: {l['question'][:50]}...")

    assert len(logs) > 0, "Audit logs should not be empty"
    recent_roles = [l.get("user_role") for l in logs[:4]]
    recent_access = [l.get("access_status") for l in logs[:4]]
    assert "OPERATIONS" in recent_roles or "CLINICAL" in recent_roles, "Audit logs must store user_role"
    assert "FILTERED" in recent_access or "GRANTED" in recent_access, "Audit logs must store access_status"
    print("  --> PASS: Audit logs correctly record user_role and access_status.")

    print("\n" + "=" * 70)
    print("  ALL PHASE 7 RBAC TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_rbac_scenarios()
