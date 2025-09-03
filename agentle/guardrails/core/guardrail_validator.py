"""
Classe base para validadores de guardrail.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from agentle.guardrails.core.guardrail_result import GuardrailResult, GuardrailAction


class GuardrailValidator(ABC):
    """
    Classe base abstrata para todos os validadores de guardrail.

    Attributes:
        name: Nome único do validador
        priority: Prioridade de execução (0 = maior prioridade)
        enabled: Se o validador está habilitado
        config: Configuração específica do validador
    """

    def __init__(
        self,
        name: str,
        priority: int = 100,
        enabled: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.priority = priority
        self.enabled = enabled
        self.config = config or {}

    @abstractmethod
    async def validate_async(
        self, content: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """
        Valida o conteúdo de forma assíncrona.

        Args:
            content: Conteúdo a ser validado
            context: Contexto adicional para a validação

        Returns:
            GuardrailResult com a decisão de validação
        """
        pass

    def validate(
        self, content: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """
        Valida o conteúdo de forma síncrona.
        """
        import asyncio

        return asyncio.run(self.validate_async(content, context))

    async def _time_validation(
        self, content: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """
        Wrapper que mede o tempo de validação.
        """
        start_time = time.perf_counter()
        try:
            result = await self.perform_validation(content, context)
            result.processing_time_ms = (time.perf_counter() - start_time) * 1000
            result.validator_name = self.name
            return result
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            return GuardrailResult(
                action=GuardrailAction.BLOCK,
                confidence=1.0,
                reason=f"Validation error in {self.name}: {str(e)}",
                validator_name=self.name,
                processing_time_ms=processing_time,
                metadata={"error": str(e)},
            )

    @abstractmethod
    async def perform_validation(
        self, content: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """
        Implementação específica da validação.
        Deve ser implementada por cada validador concreto.
        """
        pass
