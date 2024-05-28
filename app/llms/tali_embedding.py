from typing import List
import requests
from langchain.schema.embeddings import Embeddings
from pydantic import BaseModel
from app.config.config import settings


class TaliAPIEmbeddings(BaseModel, Embeddings):
    """Embed texts using the HuggingFace API.

    Requires a HuggingFace Inference API key and a model name.
    """

    @property
    def _api_url(self) -> str:
        return (
            f"http://{settings.EMBEDDING_HOST}:{settings.EMBEDDING_PORT}/v1/embeddings"
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Get the embeddings for a list of texts.
        """
        response = requests.post(
            self._api_url,
            json=texts,
        )
        return response.json()

    def embed_query(self, text: str) -> List[float]:
        """Compute query embeddings using a HuggingFace transformer model.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        return self.embed_documents([text])[0]
