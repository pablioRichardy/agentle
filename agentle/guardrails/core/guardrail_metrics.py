"""
Métricas para monitoramento do sistema de guardrails.
"""

from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime

from agentle.guardrails.core.guardrail_result import GuardrailResult


@dataclass
class GuardrailMetrics:
    """
    Métricas de performance e comportamento dos guardrails.
    """

    total_validations: int = 0
    input_validations: int = 0
    output_validations: int = 0

    total_blocks: int = 0
    total_modifications: int = 0
    total_warnings: int = 0

    total_processing_time_ms: float = 0.0
    average_processing_time_ms: float = 0.0

    validator_metrics: Dict[str, Dict[str, int]] = field(default_factory=dict)
    block_reasons: Dict[str, int] = field(default_factory=dict)

    cache_hits: int = 0
    cache_misses: int = 0

    errors: List[str] = field(default_factory=list)

    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def cache_hit_rate(self) -> float:
        """Taxa de acerto do cache."""
        total_cache_attempts = self.cache_hits + self.cache_misses
        if total_cache_attempts == 0:
            return 0.0
        return (self.cache_hits / total_cache_attempts) * 100

    @property
    def block_rate(self) -> float:
        """Taxa de bloqueio."""
        if self.total_validations == 0:
            return 0.0
        return (self.total_blocks / self.total_validations) * 100

    def update_validation_metrics(
        self, validator_name: str, result: GuardrailResult
    ) -> None:
        """Atualiza métricas baseadas em um resultado de validação."""
        from agentle.guardrails.core.guardrail_result import GuardrailAction

        self.total_validations += 1
        self.total_processing_time_ms += result.processing_time_ms
        self.average_processing_time_ms = (
            self.total_processing_time_ms / self.total_validations
        )

        # Atualizar métricas por validador
        if validator_name not in self.validator_metrics:
            self.validator_metrics[validator_name] = {
                "total": 0,
                "blocks": 0,
                "modifications": 0,
                "warnings": 0,
            }

        self.validator_metrics[validator_name]["total"] += 1

        # Atualizar contadores por ação
        if result.action == GuardrailAction.BLOCK:
            self.total_blocks += 1
            self.validator_metrics[validator_name]["blocks"] += 1
            self.block_reasons[result.reason] = (
                self.block_reasons.get(result.reason, 0) + 1
            )
        elif result.action == GuardrailAction.MODIFY:
            self.total_modifications += 1
            self.validator_metrics[validator_name]["modifications"] += 1
        elif result.action == GuardrailAction.WARN:
            self.total_warnings += 1
            self.validator_metrics[validator_name]["warnings"] += 1

        self.last_updated = datetime.now()
