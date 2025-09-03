"""
Exceções específicas para o sistema de guardrails.
"""

from typing import Any, Dict, Optional
from agentle.guardrails.core.guardrail_result import GuardrailResult


class GuardrailError(Exception):
    """Exceção base para erros de guardrail."""

    def __init__(
        self,
        message: str,
        validator_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.validator_name = validator_name
        self.metadata = metadata or {}


class GuardrailViolationError(GuardrailError):
    """Exceção lançada quando um guardrail é violado e deve bloquear a execução."""

    def __init__(self, result: GuardrailResult):
        super().__init__(
            message=result.reason,
            validator_name=result.validator_name,
            metadata=result.metadata,
        )
        self.result = result
        self.confidence = result.confidence
