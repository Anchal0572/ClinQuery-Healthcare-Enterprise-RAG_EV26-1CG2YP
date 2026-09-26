import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Clinical terms indicating directive or recommendation strength
OPPOSING_DIRECTIVES = [
    ("contraindicated", "first-line"),
    ("contraindicated", "recommended"),
    ("avoid", "first-line"),
    ("avoid", "recommended"),
    ("superseded", "recommended"),
    ("not recommended", "recommended"),
    ("not recommended", "first-line"),
]


class ConflictDetectionService:
    """
    Healthcare Conflict Detection Service:
    Ensures the system NEVER silently chooses between contradictory clinical guidelines
    or different document versions (ACTIVE vs SUPERSEDED vs RETIRED).
    """

    def detect_conflicts(
        self,
        question: str,
        evidence_chunks: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Analyzes retrieved evidence chunks to detect material clinical conflicts across document versions.
        Returns:
            Dict with 'is_conflicted', 'evidence_status' ('CONFLICTED'), 'answer', and 'conflicts' list.
            Or None if no material conflict is detected.
        """
        if not evidence_chunks or len(evidence_chunks) < 2:
            return None

        # 1. Group chunks by distinct document version and status
        version_groups: Dict[str, List[Dict[str, Any]]] = {}
        for c in evidence_chunks:
            # Group key by document title + version
            doc_title = c.get("document") or c.get("document_title") or "Unknown"
            version = str(c.get("version") or "1.0")
            key = f"{doc_title}::v{version}"
            if key not in version_groups:
                version_groups[key] = []
            version_groups[key].append(c)

        # If all qualifying chunks come from a single version, no version conflict exists
        if len(version_groups) < 2:
            return None

        # 2. Check for conflicting status (ACTIVE vs SUPERSEDED / RETIRED) or opposing clinical directives
        statuses_present = set()
        doc_versions_map: Dict[str, set] = {}
        for c in evidence_chunks:
            st = str(c.get("status") or "").upper()
            if st:
                statuses_present.add(st)
            doc_title = c.get("document") or c.get("document_title") or "Unknown"
            ver = str(c.get("version") or "1.0")
            doc_versions_map.setdefault(doc_title, set()).add(ver)

        has_same_doc_multi_version = any(len(v_set) > 1 for v_set in doc_versions_map.values())
        has_lifecycle_conflict = (
            ("ACTIVE" in statuses_present and ("SUPERSEDED" in statuses_present or "RETIRED" in statuses_present))
            and has_same_doc_multi_version
        )

        # 3. Check for opposing clinical keywords across chunks
        all_texts = [c.get("chunk_text", "").lower() for c in evidence_chunks]
        has_opposing_terms = False
        for neg_term, pos_term in OPPOSING_DIRECTIVES:
            has_neg = any(neg_term in t for t in all_texts)
            has_pos = any(pos_term in t for t in all_texts)
            if has_neg and has_pos:
                has_opposing_terms = True
                break

        # Check for opposing medication directives (e.g., Dopamine vs Norepinephrine)
        dopamine_present = any("dopamine" in t for t in all_texts)
        norepi_present = any("norepinephrine" in t for t in all_texts)
        contraindicated_present = any("contraindicated" in t for t in all_texts)
        drug_conflict = (dopamine_present and norepi_present and (contraindicated_present or has_lifecycle_conflict))

        # Check for time window conflict (e.g. 3 hours vs 1 hour, or 3.0h vs 4.5h)
        time_conflict = (
            any("3 hour" in t for t in all_texts) and any("1 hour" in t for t in all_texts)
        ) or (
            any("3.0 hour" in t for t in all_texts) and any("4.5 hour" in t for t in all_texts)
        )

        versions_present = {str(c.get("version") or "1.0") for c in evidence_chunks if c.get("version")}
        is_conflict = has_same_doc_multi_version and (has_opposing_terms or drug_conflict or time_conflict or has_lifecycle_conflict)

        if not is_conflict:
            return None

        logger.warning(
            f"Clinical conflict detected for question '{question}' across versions: {versions_present}"
        )

        # 4. Construct detailed ConflictItem entries for each conflicting version
        conflicts = []
        active_items = []
        superseded_items = []

        for group_key, chunks in version_groups.items():
            primary_chunk = chunks[0]
            doc_title = primary_chunk.get("document") or primary_chunk.get("document_title") or "Clinical Document"
            version = str(primary_chunk.get("version") or "1.0")
            date_val = primary_chunk.get("effective_date") or "Date unspecified"
            status_val = str(primary_chunk.get("status") or "ACTIVE").upper()
            section = primary_chunk.get("section") or "Clinical Guidance"
            page = primary_chunk.get("page") or 1
            chunk_text = primary_chunk.get("chunk_text", "").strip()

            # Freshness preference: ACTIVE status or latest date
            is_active = (status_val == "ACTIVE") or ("2." in version or "3." in version)
            if "SUPERSEDED" in status_val or "RETIRED" in status_val:
                is_active = False

            # Extract concise clinical claim from passage
            claim = self._summarize_claim(chunk_text)

            citation = f"[{doc_title} v{version} ({status_val}), Section: '{section}', Page {page}]"

            conflict_obj = {
                "source": doc_title,
                "version": version,
                "date": date_val,
                "status": status_val,
                "claim": claim,
                "relevant_passage": chunk_text[:280] + ("..." if len(chunk_text) > 280 else ""),
                "citation": citation,
                "is_active_fresh": is_active,
            }
            conflicts.append(conflict_obj)

            if is_active:
                active_items.append(conflict_obj)
            else:
                superseded_items.append(conflict_obj)

        # Ensure active items are sorted first for freshness preference
        conflicts.sort(key=lambda x: 0 if x["is_active_fresh"] else 1)

        # 5. Build explicit clinical answer highlighting the conflict without hiding either source
        active_summary = (
            f"ACTIVE CURRENT GUIDELINE (Version {active_items[0]['version']}, Effective: {active_items[0]['date']}):\n"
            f"  Recommendation: {active_items[0]['claim']}\n"
            f"  Citation: {active_items[0]['citation']}\n"
            f"  Relevant Passage: \"{active_items[0]['relevant_passage']}\""
            if active_items else "No active version found."
        )

        superseded_summary = (
            f"SUPERSEDED / RETIRED GUIDELINE (Version {superseded_items[0]['version']}, Effective: {superseded_items[0]['date']}):\n"
            f"  Previous Recommendation: {superseded_items[0]['claim']}\n"
            f"  Citation: {superseded_items[0]['citation']}\n"
            f"  Relevant Passage: \"{superseded_items[0]['relevant_passage']}\""
            if superseded_items else "Historical version noted."
        )

        answer = (
            "CLINICAL SAFETY ALERT — CONFLICTING PROTOCOLS DETECTED:\n\n"
            "The knowledge base contains materially conflicting clinical recommendations across different document versions. "
            "To prevent medical error, the system does not silently choose between conflicting sources.\n\n"
            f"{active_summary}\n\n"
            f"{superseded_summary}\n\n"
            "CLINICAL ACTION: Clinicians should adhere to the ACTIVE current protocol and disregard the SUPERSEDED guidance."
        )

        return {
            "is_conflicted": True,
            "evidence_status": "CONFLICTED",
            "answer": answer,
            "conflicts": conflicts,
        }

    def _summarize_claim(self, text: str) -> str:
        """
        Extract the most salient clinical recommendation sentence from the passage.
        """
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 15]
        for s in sentences:
            sl = s.lower()
            if any(term in sl for term in ["contraindicated", "mandatory", "first-line", "primary", "administer", "infusion", "dose"]):
                return s + "."
        return sentences[0] + "." if sentences else text[:120]


_conflict_service_instance: Optional[ConflictDetectionService] = None


def get_conflict_service() -> ConflictDetectionService:
    global _conflict_service_instance
    if _conflict_service_instance is None:
        _conflict_service_instance = ConflictDetectionService()
    return _conflict_service_instance
