import logging
from fastapi import APIRouter, status
from app.services.evaluation_service import get_latest_evaluation, run_full_evaluation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])


@router.get("", status_code=status.HTTP_200_OK, summary="Get latest RAG benchmark evaluation metrics")
def get_evaluation():
    """
    Returns the real evaluation metrics calculated from the 15 synthetic healthcare evaluation dataset:
    - retrieval success
    - citation presence
    - grounded answer rate
    - refusal accuracy
    - access-control accuracy
    """
    return get_latest_evaluation()


@router.post("/run", status_code=status.HTTP_200_OK, summary="Trigger live execution of full 15-question evaluation")
def run_evaluation():
    """
    Triggers a live execution of all 15 synthetic questions against the active FastAPI RAG engine,
    Qdrant vector store, and role-based access control filters. Returns freshly calculated metrics.
    """
    return run_full_evaluation()
