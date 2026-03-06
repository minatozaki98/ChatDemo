# backend/chat.py
from openai import AzureOpenAI

from backend.config import get_settings
from backend.models import Message

_settings = get_settings()

client = AzureOpenAI(
    azure_endpoint=_settings.azure_openai_endpoint,
    api_key=_settings.azure_openai_api_key,
    api_version=_settings.azure_openai_api_version,
)


def get_reply(messages: list[Message]) -> str:
    response = client.chat.completions.create(
        model=_settings.azure_openai_deployment,
        messages=[{"role": m.role, "content": m.content} for m in messages],  # type: ignore[misc]
    )
    content = response.choices[0].message.content
    return content if content is not None else ""
