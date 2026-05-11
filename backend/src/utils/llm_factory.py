from langchain_openai import ChatOpenAI

from src.config import settings


def get_llm(temperature: float = 0.3, streaming: bool = False) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=temperature,
        streaming=streaming,
    )
