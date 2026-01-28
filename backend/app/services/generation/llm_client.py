"""LLM client for OpenAI GPT-4o-mini."""

from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """
    OpenAI LLM client for RAG generation.

    Uses GPT-4o-mini for cost-effective, high-quality responses.
    Supports streaming for real-time response delivery.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        """
        Initialize LLM client.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Model name (defaults to settings.openai_llm_model)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_llm_model

        self.client = AsyncOpenAI(api_key=self.api_key)

        logger.info("llm_client_initialized", model=self.model)

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> str:
        """
        Generate a response (non-streaming).

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Response randomness (0-1)
            max_tokens: Maximum response tokens

        Returns:
            Generated response text
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content or ""

        logger.debug(
            "llm_generation_complete",
            model=self.model,
            input_messages=len(messages),
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )

        return content

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Response randomness (0-1)
            max_tokens: Maximum response tokens

        Yields:
            Response text chunks
        """
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

        logger.debug("llm_stream_complete", model=self.model)


# RAG System Prompt
RAG_SYSTEM_PROMPT = """You are CloudSignal's internal knowledge assistant. Your role is to help employees find information from the company's internal documentation.

CRITICAL RULES:
1. ONLY answer based on the provided context documents. Never use external knowledge.
2. If the context doesn't contain relevant information, say "I don't have information about that in the available documents."
3. ALWAYS cite your sources using the document titles provided in the context.
4. Be concise and direct - this is an enterprise tool for busy professionals.
5. NEVER reveal document titles or content that wasn't provided in the context.
6. NEVER speculate about documents you cannot access.
7. If asked about topics outside the provided context, redirect to the relevant document types if known.

CITATION FORMAT:
When citing sources, use this format: [Document Title]

SECURITY NOTE:
The documents provided have already been filtered based on the user's access level. You should treat all provided documents as authorized for the current user. Never mention access restrictions or suggest that some documents may be hidden."""


def build_rag_prompt(
    query: str,
    context_documents: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """
    Build RAG prompt with context documents.

    Args:
        query: User's question
        context_documents: Retrieved documents with text and metadata

    Returns:
        List of messages for the LLM
    """
    # Build context section
    context_parts = []
    for i, doc in enumerate(context_documents, 1):
        title = doc.get("title", f"Document {i}")
        text = doc.get("text", "")
        doc_type = doc.get("doc_type", "document")
        department = doc.get("department", "")

        context_parts.append(
            f"[{i}] {title} ({doc_type}{', ' + department if department else ''})\n{text}"
        )

    context_text = "\n\n---\n\n".join(context_parts)

    messages = [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Based on the following context documents, please answer this question:

QUESTION: {query}

CONTEXT DOCUMENTS:
{context_text}

Remember to cite your sources using [Document Title] format.""",
        },
    ]

    return messages
