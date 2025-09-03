"""
Validador de toxicidade usando análise de sentimento simples.
"""

from typing import Any
from agentle.guardrails.core.input_guardrail_validator import InputGuardrailValidator
from agentle.guardrails.core.output_guardrail_validator import OutputGuardrailValidator
from agentle.guardrails.core.guardrail_result import GuardrailResult, GuardrailAction


class ToxicityValidator(InputGuardrailValidator, OutputGuardrailValidator):
    """
    Validador de toxicidade que detecta linguagem tóxica ou ofensiva.

    Em produção, você integraria com APIs como:
    - Google Cloud Natural Language API
    - Azure Content Moderator
    - Hugging Face Transformers para modelos de toxicidade
    """

    def __init__(
        self,
        priority: int = 15,
        enabled: bool = True,
        toxicity_threshold: float = 0.7,
        config: dict[str, Any] | None = None,
    ):
        super().__init__(
            name="toxicity", priority=priority, enabled=enabled, config=config or {}
        )

        self.toxicity_threshold = toxicity_threshold

        # Palavras tóxicas básicas - em produção, use um modelo ML
        self.toxic_words: list[str] = [
            "idiota",
            "estúpido",
            "burro",
            "imbecil",
            "hate",
            "stupid",
            "idiot",
            "dumb",
        ]

        # Padrões tóxicos
        self.toxic_patterns = ["você é um", "you are so", "vai se", "go kill yourself"]

    async def perform_validation(
        self, content: str, context: dict[str, Any] | None = None
    ) -> GuardrailResult:
        """
        Executa análise de toxicidade no conteúdo.
        """
        toxicity_score = self._calculate_toxicity_score(content)

        if toxicity_score >= self.toxicity_threshold:
            return GuardrailResult(
                action=GuardrailAction.BLOCK,
                confidence=toxicity_score,
                reason=f"High toxicity detected (score: {toxicity_score:.2f})",
                validator_name=self.name,
                metadata={
                    "toxicity_score": toxicity_score,
                    "threshold": self.toxicity_threshold,
                },
            )
        elif toxicity_score >= 0.4:  # Warning threshold
            return GuardrailResult(
                action=GuardrailAction.WARN,
                confidence=toxicity_score,
                reason=f"Moderate toxicity detected (score: {toxicity_score:.2f})",
                validator_name=self.name,
                metadata={"toxicity_score": toxicity_score},
            )

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            confidence=1.0 - toxicity_score,
            reason="Content passed toxicity validation",
            validator_name=self.name,
            metadata={"toxicity_score": toxicity_score},
        )

    def _calculate_toxicity_score(self, content: str) -> float:
        """
        Calcula pontuação de toxicidade simples.
        Em produção, use um modelo ML adequado.
        """
        content_lower = content.lower()
        score = 0.0

        # Verificar palavras tóxicas
        for word in self.toxic_words:
            if word in content_lower:
                score += 0.3

        # Verificar padrões tóxicos
        for pattern in self.toxic_patterns:
            if pattern in content_lower:
                score += 0.5

        # Verificar excesso de maiúsculas (indicativo de agressividade)
        if len(content) > 10:
            uppercase_ratio = sum(1 for c in content if c.isupper()) / len(content)
            if uppercase_ratio > 0.6:
                score += 0.2

        # Verificar excesso de pontuação
        punct_count = sum(1 for c in content if c in "!?")
        if punct_count > 3:
            score += 0.1

        return min(score, 1.0)
