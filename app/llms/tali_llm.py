from langchain_community.chat_models import ChatOpenAI
from app.config.config import settings
from typing import (
    Optional,
    Tuple,
    Union,
)


class TaliLLM(ChatOpenAI):
    openai_api_base = f"http://{settings.LLM_HOST}:{settings.LLM_PORT}/v1"
    openai_api_key = "123456"
    model_name = "gpt-4"
    request_timeout: Optional[Union[float, Tuple[float, float]]] = 120.0
    max_retries: int = 2
