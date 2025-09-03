"""
Validador específico para entrada (input) do usuário.
"""

from typing import Any, Dict, Optional
from agentle.guardrails.core.guardrail_result import GuardrailResult
from agentle.guardrails.core.guardrail_validator import GuardrailValidator


class InputGuardrailValidator(GuardrailValidator):
    """
    Classe base para validadores de entrada (input).

    Validadores de entrada processam e validam o conteúdo antes que chegue ao modelo de IA.
    Isso inclui verificações de:
    - Segurança de conteúdo
    - Detecção de injeção de prompt
    - Validação de formato
    - Detecção de PII
    """

    def __init__(
        self,
        name: str,
        priority: int = 100,
        enabled: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            name=f"input_{name}", priority=priority, enabled=enabled, config=config
        )

    async def validate_async(
        self, content: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """
        Valida entrada do usuário antes do processamento pelo modelo.

        Args:
            content: Input do usuário
            context: Contexto adicional (ex: histórico de conversa, metadados do usuário)
        """
        return await self._time_validation(content, context)
