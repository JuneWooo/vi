
import chromadb
from app.llms.tali_embedding import TaliAPIEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from chromadb.api.models.Collection import Collection
from app.config.config import settings


client = chromadb.HttpClient(
    host=settings.CHROMA_HOST,
    port=settings.CHROMA_PORT
)

embedding_function = TaliAPIEmbeddings()
MAPPING_COLLECTION = client.get_or_create_collection(
    "bz_mapping_doc")
KNOWLEGE_BASE_COLLECTION = client.get_or_create_collection(
    "bz_knowgele_base_doc")


def get_langchain_chroma(collection_name: Collection) -> Chroma:

    return Chroma(
        collection_name=collection_name.name,
        client=client,
        embedding_function=embedding_function,
        relevance_score_fn=lambda distance: 1.0 - distance / 2
    )
