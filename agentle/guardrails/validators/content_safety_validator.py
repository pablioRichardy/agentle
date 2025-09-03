"""
Validador de segurança de conteúdo.
"""

import re
from typing import Any, Dict, Optional, List
from agentle.guardrails.core.input_guardrail_validator import InputGuardrailValidator
from agentle.guardrails.core.output_guardrail_validator import OutputGuardrailValidator
from agentle.guardrails.core.guardrail_result import GuardrailResult, GuardrailAction


class ContentSafetyValidator(InputGuardrailValidator, OutputGuardrailValidator):
    """
    Validador de segurança de conteúdo que detecta:
    - Linguagem ofensiva
    - Conteúdo violento
    - Discurso de ódio
    - Conteúdo sexual inapropriado
    """

    def __init__(
        self,
        priority: int = 10,
        enabled: bool = True,
        custom_blocked_terms: Optional[List[str]] = None,
        severity_threshold: float = 0.7,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            name="content_safety",
            priority=priority,
            enabled=enabled,
            config=config or {},
        )

        self.custom_blocked_terms = custom_blocked_terms or []
        self.severity_threshold = severity_threshold

        # Termos básicos de exemplo - em produção, use uma lista mais abrangente
        self.blocked_terms = [
            # Violência
            "kill",
            "murder",
            "violence",
            "harm",
            "hurt",
            "attack",
            # Drogas
            "cocaine",
            "heroin",
            "meth",
            "drugs",
            # Outros termos sensíveis
            "suicide",
            "self-harm",
        ] + self.custom_blocked_terms

        # Padrões regex para detecção mais sofisticada
        self.offensive_patterns = [
            r"\b(hate|hatred)\s+(towards?|against|for)\b",
            r"\b(kill|murder|hurt)\s+(yourself|himself|herself)\b",
            r"\binstructions?\s+(?:to|for|on)\s+(?:make|create|build)\s+(?:bomb|weapon|explosive)\b",
        ]

    async def perform_validation(
        self, content: str, context: Optional[Dict[str, Any]] = None
    ) -> GuardrailResult:
        """
        Executa validação de segurança de conteúdo.
        """
        content_lower = content.lower()
        violations: list[str] = []
        severity_score = 0.0

        # Verificar termos bloqueados
        for term in self.blocked_terms:
            if term.lower() in content_lower:
                violations.append(f"Blocked term detected: {term}")
                severity_score += 0.3

        # Verificar padrões regex
        for pattern in self.offensive_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                violations.append("Offensive pattern detected")
                severity_score += 0.5

        # Normalizar pontuação de severidade
        severity_score = min(severity_score, 1.0)

        if severity_score >= self.severity_threshold:
            return GuardrailResult(
                action=GuardrailAction.BLOCK,
                confidence=severity_score,
                reason=f"Content safety violation: {'; '.join(violations)}",
                validator_name=self.name,
                metadata={
                    "violations": violations,
                    "severity_score": severity_score,
                    "threshold": self.severity_threshold,
                },
            )
        elif violations:
            return GuardrailResult(
                action=GuardrailAction.WARN,
                confidence=severity_score,
                reason=f"Potential content safety issue: {'; '.join(violations)}",
                validator_name=self.name,
                metadata={"violations": violations, "severity_score": severity_score},
            )

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            confidence=1.0 - severity_score,
            reason="Content passed safety validation",
            validator_name=self.name,
        )
