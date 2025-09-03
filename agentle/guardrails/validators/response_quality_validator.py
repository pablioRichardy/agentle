# agentle/guardrails/validators/response_quality_validator.py
"""
Validador de qualidade de resposta.
"""

import re
from typing import Any, Dict, Optional
from agentle.guardrails.core.output_guardrail_validator import OutputGuardrailValidator
from agentle.guardrails.core.guardrail_result import GuardrailResult, GuardrailAction


class ResponseQualityValidator(OutputGuardrailValidator):
    """
    Validador que avalia a qualidade da resposta gerada:
    - Comprimento adequado
    - Estrutura e coerência
    - Relevância
    - Completude
    """

    def __init__(
        self,
        priority: int = 50,
        enabled: bool = True,
        min_length: int = 10,
        max_length: int = 10000,
        require_punctuation: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            name="response_quality",
            priority=priority,
            enabled=enabled,
            config=config or {},
        )

        self.min_length = min_length
        self.max_length = max_length
        self.require_punctuation = require_punctuation

    async def perform_validation(
        self, content: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """
        Executa validação de qualidade da resposta.
        """
        quality_issues: list[str] = []
        quality_score = 1.0

        # Verificar comprimento
        if len(content) < self.min_length:
            quality_issues.append(
                f"Response too short ({len(content)} < {self.min_length})"
            )
            quality_score -= 0.5

        if len(content) > self.max_length:
            quality_issues.append(
                f"Response too long ({len(content)} > {self.max_length})"
            )
            quality_score -= 0.3

        # Verificar estrutura básica
        if content.strip() == "":
            quality_issues.append("Response is empty")
            quality_score = 0.0

        # Verificar se tem pontuação (indicativo de estrutura)
        if self.require_punctuation and len(content) > 20:
            if not re.search(r"[.!?]", content):
                quality_issues.append("Response lacks proper punctuation")
                quality_score -= 0.2

        # Verificar repetição excessiva
        words = content.split()
        if len(words) > 10:
            unique_words = set(words)
            repetition_ratio = len(words) / len(unique_words)
            if repetition_ratio > 3.0:  # Muita repetição
                quality_issues.append(
                    f"Excessive word repetition (ratio: {repetition_ratio:.2f})"
                )
                quality_score -= 0.3

        # Verificar se parece ser uma resposta válida
        non_word_chars = sum(
            1
            for c in content
            if not (c.isalnum() or c.isspace() or c in ".,!?;:-()[]{}\"'")
        )
        if len(content) > 0:
            non_word_ratio = non_word_chars / len(content)
            if non_word_ratio > 0.3:
                quality_issues.append(
                    f"Too many non-standard characters ({non_word_ratio:.2%})"
                )
                quality_score -= 0.2

        # Verificar frases incompletas óbvias
        if content.strip().endswith(("...", "and", "but", "or", "so", "because")):
            quality_issues.append("Response appears to be incomplete")
            quality_score -= 0.4

        quality_score = max(quality_score, 0.0)

        if quality_score < 0.3:
            return GuardrailResult(
                action=GuardrailAction.BLOCK,
                confidence=1.0 - quality_score,
                reason=f"Low quality response: {'; '.join(quality_issues)}",
                validator_name=self.name,
                metadata={
                    "quality_issues": quality_issues,
                    "quality_score": quality_score,
                    "response_length": len(content),
                    "word_count": len(content.split()),
                },
            )
        elif quality_score < 0.7:
            return GuardrailResult(
                action=GuardrailAction.WARN,
                confidence=0.8,
                reason=f"Potential quality issues: {'; '.join(quality_issues)}",
                validator_name=self.name,
                metadata={
                    "quality_issues": quality_issues,
                    "quality_score": quality_score,
                },
            )

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            confidence=quality_score,
            reason="Response passed quality validation",
            validator_name=self.name,
            metadata={
                "quality_score": quality_score,
                "response_length": len(content),
                "word_count": len(content.split()),
            },
        )
