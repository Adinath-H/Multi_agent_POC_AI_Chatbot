import os
import time

from groq import Groq, RateLimitError

from ..config import GROQ_API_KEY, GROQ_MODEL


class LLMService:
    """Small, rate-limit-friendly wrapper around Groq Chat Completions."""

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.model = GROQ_MODEL
        # Keep requests small enough for free/low TPM accounts.
        self.max_completion_tokens = int(os.getenv("GROQ_MAX_COMPLETION_TOKENS", "1400"))
        self.max_retries = int(os.getenv("GROQ_MAX_RETRIES", "1"))

    def available(self) -> bool:
        return self.client is not None

    def ask(self, prompt: str, system: str = "You are a helpful enterprise AI assistant.") -> str:
        if not self.client:
            return self._fallback(prompt)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        return self._chat(messages, temperature=0.2)

    def ask_messages(self, messages: list[dict], temperature: float = 0.2) -> str:
        if not self.client:
            prompt = "\n".join(str(m.get("content", "")) for m in messages)
            return self._fallback(prompt)
        return self._chat(messages, temperature=temperature)

    def _chat(self, messages: list[dict], temperature: float) -> str:
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_completion_tokens": self.max_completion_tokens,
                }

                # GPT-OSS reasoning can consume a large part of the TPM budget.
                # Groq supports include_reasoning=False for GPT-OSS models.
                if self.model.startswith("openai/gpt-oss"):
                    kwargs["include_reasoning"] = False
                    kwargs["reasoning_effort"] = "low"

                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ""

            except RateLimitError as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break

                # Groq may expose retry-after in response headers.
                delay = 2
                response = getattr(exc, "response", None)
                headers = getattr(response, "headers", {}) or {}
                retry_after = headers.get("retry-after")
                if retry_after:
                    try:
                        delay = min(max(int(float(retry_after)) + 1, 1), 20)
                    except (TypeError, ValueError):
                        delay = 2
                time.sleep(delay)

        # Return a usable POC response instead of crashing FastAPI with HTTP 500.
        return (
            "Groq rate limit reached for this request. "
            "The POC automatically keeps the prompt/output small; please retry the same request "
            "after the current TPM window resets.\n\n"
            f"Model: {self.model}\n"
            f"Details: {last_error}"
        )

    def _fallback(self, prompt: str) -> str:
        lower = prompt.lower()
        if "12-slide" in lower or "12 slide" in lower or "slides" in lower:
            return "\n\n".join(
                [
                    "[SLIDE 1]\nGenerative AI Trends\n- Executive overview\n- Market direction\n- Business impact",
                    "[SLIDE 2]\nExecutive Summary\n- GenAI adoption is expanding\n- Governance is becoming essential\n- Enterprise value depends on use-case selection",
                    "[SLIDE 3]\nKey Technology Trends\n- Large language models\n- Multimodal AI\n- Retrieval-augmented generation",
                    "[SLIDE 4]\nEnterprise Use Cases\n- Knowledge assistants\n- Customer support\n- Document automation",
                    "[SLIDE 5]\nRAG Architecture\n- Ingestion\n- Retrieval\n- Grounded generation",
                    "[SLIDE 6]\nAgentic AI\n- Planning\n- Tool use\n- Multi-step workflows",
                    "[SLIDE 7]\nSecurity and Governance\n- Access control\n- Data protection\n- Auditability",
                    "[SLIDE 8]\nImplementation Roadmap\n- Discover\n- Pilot\n- Scale",
                    "[SLIDE 9]\nOperating Model\n- Business owner\n- AI engineering\n- Governance",
                    "[SLIDE 10]\nRisks and Mitigations\n- Hallucination -> grounding\n- Cost -> monitoring\n- Privacy -> controls",
                    "[SLIDE 11]\nSuccess Metrics\n- Adoption\n- Accuracy\n- Time saved",
                    "[SLIDE 12]\nNext Steps\n- Select two priority use cases\n- Build a pilot\n- Measure results",
                ]
            )
        return (
            "# Proposal\n\n## Executive Summary\n"
            "This proof of concept combines multi-agent orchestration, enterprise knowledge retrieval, "
            "web research, and editable document generation.\n\n"
            "## Business Context\nThe solution is designed for controlled enterprise content creation with traceability.\n\n"
            "## Approach\n1. Analyze templates.\n2. Research current information.\n3. Retrieve enterprise knowledge.\n4. Generate editable artifacts.\n5. Validate and version results.\n\n"
            "## Recommendations\nStart with a focused pilot, measure quality and time saved, then expand.\n\n"
            "## Sources\n- Assignment specification\n- Enterprise knowledge base"
        )


llm = LLMService()
