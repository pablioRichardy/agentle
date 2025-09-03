"""
Validador para detecção de informações pessoais identificáveis (PII).
"""

import re
from typing import Any
from agentle.guardrails.core.input_guardrail_validator import InputGuardrailValidator
from agentle.guardrails.core.output_guardrail_validator import OutputGuardrailValidator
from agentle.guardrails.core.guardrail_result import GuardrailResult, GuardrailAction


class PIIDetectionValidator(InputGuardrailValidator, OutputGuardrailValidator):
    """
    Validador que detecta e opcionalmente mascara informações pessoais:
    - CPF
    - Email
    - Telefone
    - Cartão de crédito
    - Outros padrões personalizados
    """

    def __init__(
        self,
        priority: int = 20,
        enabled: bool = True,
        mask_pii: bool = True,
        action_on_detection: GuardrailAction = GuardrailAction.MODIFY,
        config: dict[str, Any] | None = None,
    ):
        super().__init__(
            name="pii_detection",
            priority=priority,
            enabled=enabled,
            config=config or {},
        )

        self.mask_pii = mask_pii
        self.action_on_detection = action_on_detection

        # Padrões regex para diferentes tipos de PII
        self.pii_patterns = {
            "cpf": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone_br": r"\b(?:\+55\s?)?(?:\(?0?\d{2}\)?\s?)(?:9\d{4}[-\s]?\d{4}|\d{4}[-\s]?\d{4})\b",
            "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            "rg": r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dX]\b",
        }

    async def perform_validation(
        self, content: str, context: dict[str, Any] | None = None
    ) -> GuardrailResult:
        """
        Executa detecção de PII no conteúdo.
        """
        detected_pii: list[dict[str, Any]] = []
        modified_content = content

        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)

            for match in matches:
                detected_pii.append(
                    {
                        "type": pii_type,
                        "value": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

                if self.mask_pii:
                    # Mascarar o PII detectado
                    masked_value = self._mask_value(match.group(), pii_type)
                    modified_content = modified_content.replace(
                        match.group(), masked_value
                    )

        if detected_pii:
            return GuardrailResult(
                action=self.action_on_detection,
                confidence=0.95,
                reason=f"PII detected: {len(detected_pii)} instances of {', '.join(set(pii['type'] for pii in detected_pii))}",
                validator_name=self.name,
                modified_content=modified_content if self.mask_pii else None,
                metadata={
                    "detected_pii": detected_pii,
                    "pii_types": list(set(pii["type"] for pii in detected_pii)),
                    "masked": self.mask_pii,
                },
            )

        return GuardrailResult(
            action=GuardrailAction.ALLOW,
            confidence=0.9,
            reason="No PII detected",
            validator_name=self.name,
        )

    def _mask_value(self, value: str, pii_type: str) -> str:
        """
        Mascara um valor de PII baseado no tipo.
        """
        if pii_type == "email":
            # Mascarar email: user@domain.com -> u***@d***.com
            parts = value.split("@")
            if len(parts) == 2:
                username = parts[0]
                domain_parts = parts[1].split(".")
                masked_username = username[0] + "*" * (len(username) - 1)
                masked_domain = domain_parts[0][0] + "*" * (len(domain_parts[0]) - 1)
                return f"{masked_username}@{masked_domain}.{domain_parts[-1]}"
        elif pii_type == "cpf":
            # Mascarar CPF: 123.456.789-01 -> ***.***.***-**
            return "***.***.***-**"
        elif pii_type == "phone_br":
            # Mascarar telefone: manter apenas os últimos 4 dígitos
            digits_only = re.sub(r"\D", "", value)
            if len(digits_only) >= 4:
                return "*" * (len(digits_only) - 4) + digits_only[-4:]
        elif pii_type == "credit_card":
            # Mascarar cartão: manter apenas os últimos 4 dígitos
            digits_only = re.sub(r"\D", "", value)
            if len(digits_only) >= 4:
                return "**** **** **** " + digits_only[-4:]

        # Fallback: mascarar tudo exceto primeiro e último caractere
        if len(value) <= 2:
            return "*" * len(value)
        return value[0] + "*" * (len(value) - 2) + value[-1]
