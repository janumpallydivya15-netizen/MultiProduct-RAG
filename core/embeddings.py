from typing import List
import config

class EmbeddingService:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.EMBEDDING_MODEL_NAME
        self._model = None

    @property
    def model(self):
        """Lazy loader for SentenceTransformers model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                print(f"[EmbeddingService] Warning: Failed to load model {self.model_name}: {e}")
                return None
        return self._model

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings for a list of text strings."""
        if not texts:
            return []

        model = self.model
        if model is None:
            # Fallback zero-vectors if model failed to load
            return [[0.0] * 384 for _ in texts]

        embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return embeddings.tolist()

    def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single string query."""
        results = self.generate_embeddings([text])
        return results[0] if results else [0.0] * 384
