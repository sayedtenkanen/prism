from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr


class LLMClient:
    """LLM client with support for multiple providers and configurable models."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o",
        api_key: str = "",
        temperature: float = 0.3,
    ):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self._api_key = api_key

        secret_key = SecretStr(api_key) if api_key else None
        if provider == "openai":
            self.llm = ChatOpenAI(
                model=model,
                api_key=secret_key,
                temperature=temperature,
            )
        else:
            # Default to OpenAI for now, extend for other providers
            self.llm = ChatOpenAI(
                model=model,
                api_key=secret_key,
                temperature=temperature,
            )

    async def ainvoke(self, messages: list) -> str:
        """Invoke the LLM with a list of messages."""
        response: Any = await self.llm.ainvoke(messages)
        return str(response.content)

    async def review(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
    ) -> str:
        """Convenience method for review calls."""
        if model and model != self.model:
            # Create a new LLM with different model if needed
            secret_key = SecretStr(self._api_key) if self._api_key else None
            llm = ChatOpenAI(
                model=model,
                api_key=secret_key,
                temperature=self.temperature,
            )
            response: Any = await llm.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )
        else:
            response = await self.llm.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )
        return str(response.content)
