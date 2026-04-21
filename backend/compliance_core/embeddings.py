from openai import AsyncOpenAI

from compliance_core.config import get_settings
from compliance_core.llm import get_async_openai_client_for_llm, resolve_llm_api_key


async def embed_texts(texts: list[str]) -> list[list[float]]:
    s = get_settings()
    client: AsyncOpenAI = get_async_openai_client_for_llm(s)
    resp = await client.embeddings.create(model=s.embedding_model, input=texts)
    return [d.embedding for d in resp.data]


async def embed_query(q: str) -> list[float]:
    vecs = await embed_texts([q])
    return vecs[0]
