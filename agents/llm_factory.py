"""Deterministic mock client. No remote model providers are configured."""
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "CTCAE Adverse Event Grader"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (
            f"[{self.system_name} mock mode] No clinical analysis, CTCAE grading, "
            "external model inference, or guideline verification was performed."
        )


class LLMFactory:
    """Return an explicit mock; do not misrepresent unsupported providers."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "CTCAE Adverse Event Grader"):
        if str(provider).lower() not in {"mock", "deterministic", "test"}:
            raise ValueError("Only the local deterministic mock provider is supported")
        return MockLLM(system_name)
