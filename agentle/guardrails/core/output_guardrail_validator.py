"""
Validador específico para saída (output) do modelo.
"""

from typing import Any, Dict, Optional
from agentle.guardrails.core.guardrail_result import GuardrailResult
from agentle.guardrails.core.guardrail_validator import GuardrailValidator


class OutputGuardrailValidator(GuardrailValidator):
    """
    Classe base para validadores de saída (output).

    Validadores de saída processam e validam as respostas geradas pelo modelo antes
    de entregá-las ao usuário. Isso inclui verificações de:
    - Qualidade da resposta
    - Segurança do conteúdo
    - Precisão factual
    - Conformidade com diretrizes
    """

    def __init__(
        self,
        name: str,
        priority: int = 100,
        enabled: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            name=f"output_{name}", priority=priority, enabled=enabled, config=config
        )

    async def validate_async(
        self, content: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """
        Valida saída do modelo antes de entregá-la ao usuário.

        Args:
            content: Resposta gerada pelo modelo
            context: Contexto adicional (ex: prompt original, metadados da geração)
        """
        return await self._time_validation(content, context)
