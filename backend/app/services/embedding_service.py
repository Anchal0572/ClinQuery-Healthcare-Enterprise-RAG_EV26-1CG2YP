import logging
import hashlib
import numpy as np
from typing import List, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)

_fastembed_model_instance = None


def get_fastembed_model(model_name: str = "BAAI/bge-small-en-v1.5"):
    """
    Lazy singleton loader for FastEmbed model.
    """
    global _fastembed_model_instance
    if _fastembed_model_instance is None:
        try:
            from fastembed import TextEmbedding
            logger.info(f"Loading FastEmbed model '{model_name}'...")
            _fastembed_model_instance = TextEmbedding(model_name=model_name)
            logger.info(f"FastEmbed model '{model_name}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize FastEmbed model '{model_name}': {e}")
            raise
    return _fastembed_model_instance


class EmbeddingService:
    """
    Configurable embedding service supporting:
    - 'fastembed': Local ONNX embeddings (BAAI/bge-small-en-v1.5, default 384 dim)
    - 'gemini': Google Generative AI embeddings
    - 'openai': OpenAI embeddings
    - 'mock': Deterministic normalized vector for isolated offline testing
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        dimension: Optional[int] = None,
    ):
        settings = get_settings()
        self.provider = (provider or settings.embedding_provider).lower()
        self.model_name = model_name or settings.embedding_model
        self.dimension = dimension or settings.embedding_dimension

    def get_dimension(self) -> int:
        if self.provider == "fastembed":
            return self.dimension or 384
        elif self.provider == "gemini":
            return 768
        elif self.provider == "openai":
            return 1536
        return self.dimension or 384

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.provider == "fastembed":
            try:
                model = get_fastembed_model(self.model_name)
                # fastembed returns generator of numpy arrays
                embeddings_gen = model.embed(texts)
                return [emb.tolist() for emb in embeddings_gen]
            except Exception as e:
                logger.warning(f"FastEmbed embedding failed ({e}); falling back to deterministic embedding.")
                return [self._generate_mock_embedding(t) for t in texts]

        elif self.provider == "gemini":
            return self._embed_gemini(texts)

        elif self.provider == "openai":
            return self._embed_openai(texts)

        else:
            return [self._generate_mock_embedding(t) for t in texts]

    def embed_text(self, text: str) -> List[float]:
        results = self.embed_texts([text])
        return results[0] if results else [0.0] * self.get_dimension()

    def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Deterministic, normalized pseudo-embedding based on sha256 of text.
        Used for fast test suites or mock providers.
        """
        dim = self.get_dimension()
        hash_digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Seed pseudo-random generator with hash
        seed = int.from_bytes(hash_digest[:4], "big")
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(dim)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def _embed_gemini(self, texts: List[str]) -> List[List[float]]:
        settings = get_settings()
        if not settings.llm_api_key or settings.llm_api_key.startswith("mock"):
            logger.warning("No Gemini API key configured. Falling back to deterministic mock embedding.")
            return [self._generate_mock_embedding(t) for t in texts]

        try:
            import importlib
            genai = importlib.import_module("google.generativeai")
            genai.configure(api_key=settings.llm_api_key)
            results = []
            for text in texts:
                res = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_document",
                )
                results.append(res["embedding"])
            return results
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            return [self._generate_mock_embedding(t) for t in texts]

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        settings = get_settings()
        if not settings.llm_api_key or settings.llm_api_key.startswith("mock"):
            logger.warning("No OpenAI API key configured. Falling back to deterministic mock embedding.")
            return [self._generate_mock_embedding(t) for t in texts]

        try:
            import importlib
            openai_pkg = importlib.import_module("openai")
            client = openai_pkg.OpenAI(api_key=settings.llm_api_key)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return [self._generate_mock_embedding(t) for t in texts]


_embedding_service_instance = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance
