# agentle/guardrails/core/guardrail_config.py
"""
TypedDict para configuração de guardrails.
"""

from typing import TypedDict, NotRequired


class GuardrailConfig(TypedDict):
    """
    Configuração tipada para o sistema de guardrails.

    Attributes:
        fail_on_input_violation: Se deve falhar quando input violar guardrails (default: True)
        fail_on_output_violation: Se deve falhar quando output violar guardrails (default: False)
        log_violations: Se deve fazer log de todas as violações (default: True)
        include_metrics: Se deve incluir métricas de guardrails no resultado (default: True)
        fail_fast: Se deve parar na primeira violação encontrada (default: True)
        parallel_execution: Se deve executar validadores em paralelo (default: True)
        cache_enabled: Se deve usar cache para validações (default: True)
        max_cache_size: Tamanho máximo do cache de validações (default: 1000)
        cache_ttl_seconds: TTL do cache em segundos (default: 3600)
        enable_async_logging: Se deve fazer logging assíncrono (default: False)
        violation_callback: Nome da função callback para violações (default: None)
        metrics_callback: Nome da função callback para métricas (default: None)
        custom_error_messages: Mensagens de erro customizadas por validador (default: {})
        retry_on_error: Se deve tentar novamente em caso de erro (default: False)
        max_retries: Número máximo de tentativas em caso de erro (default: 3)
        retry_delay_seconds: Delay entre tentativas em segundos (default: 1.0)
        enable_preprocessing: Se deve habilitar pré-processamento do conteúdo (default: True)
        enable_postprocessing: Se deve habilitar pós-processamento do conteúdo (default: True)
        batch_size: Tamanho do batch para processamento em lote (default: 10)
        timeout_seconds: Timeout para validações em segundos (default: 30.0)
    """

    # Comportamento principal
    fail_on_input_violation: NotRequired[bool]
    fail_on_output_violation: NotRequired[bool]
    log_violations: NotRequired[bool]
    include_metrics: NotRequired[bool]

    # Estratégia de execução
    fail_fast: NotRequired[bool]
    parallel_execution: NotRequired[bool]

    # Cache
    cache_enabled: NotRequired[bool]
    max_cache_size: NotRequired[int]
    cache_ttl_seconds: NotRequired[int]

    # Logging e callbacks
    enable_async_logging: NotRequired[bool]
    violation_callback: NotRequired[str | None]
    metrics_callback: NotRequired[str | None]

    # Customização
    custom_error_messages: NotRequired[dict[str, str]]

    # Retry e error handling
    retry_on_error: NotRequired[bool]
    max_retries: NotRequired[int]
    retry_delay_seconds: NotRequired[float]

    # Processamento
    enable_preprocessing: NotRequired[bool]
    enable_postprocessing: NotRequired[bool]
    batch_size: NotRequired[int]

    # Performance
    timeout_seconds: NotRequired[float]


# Configurações padrão para facilitar o uso
DEFAULT_GUARDRAIL_CONFIG: GuardrailConfig = {
    # Comportamento principal
    "fail_on_input_violation": True,
    "fail_on_output_violation": False,
    "log_violations": True,
    "include_metrics": True,
    # Estratégia de execução
    "fail_fast": True,
    "parallel_execution": True,
    # Cache
    "cache_enabled": True,
    "max_cache_size": 1000,
    "cache_ttl_seconds": 3600,
    # Logging e callbacks
    "enable_async_logging": False,
    "violation_callback": None,
    "metrics_callback": None,
    # Customização
    "custom_error_messages": {},
    # Retry e error handling
    "retry_on_error": False,
    "max_retries": 3,
    "retry_delay_seconds": 1.0,
    # Processamento
    "enable_preprocessing": True,
    "enable_postprocessing": True,
    "batch_size": 10,
    # Performance
    "timeout_seconds": 30.0,
}


# Configurações pré-definidas para diferentes cenários
DEVELOPMENT_GUARDRAIL_CONFIG: GuardrailConfig = {
    "fail_on_input_violation": False,
    "fail_on_output_violation": False,
    "log_violations": True,
    "include_metrics": True,
    "fail_fast": False,
    "parallel_execution": False,  # Para debugging sequencial
    "cache_enabled": False,  # Sempre reprocessar em dev
    "enable_async_logging": False,
    "retry_on_error": True,
    "max_retries": 1,
    "timeout_seconds": 60.0,  # Mais tempo para debugging
}


PRODUCTION_GUARDRAIL_CONFIG: GuardrailConfig = {
    "fail_on_input_violation": True,
    "fail_on_output_violation": True,
    "log_violations": True,
    "include_metrics": False,  # Menos overhead em produção
    "fail_fast": True,
    "parallel_execution": True,
    "cache_enabled": True,
    "max_cache_size": 5000,  # Cache maior em produção
    "cache_ttl_seconds": 7200,  # 2 horas
    "enable_async_logging": True,
    "retry_on_error": False,  # Falha rápido em produção
    "timeout_seconds": 10.0,  # Timeout menor em produção
}


TESTING_GUARDRAIL_CONFIG: GuardrailConfig = {
    "fail_on_input_violation": True,
    "fail_on_output_violation": True,
    "log_violations": False,  # Menos logs em testes
    "include_metrics": False,
    "fail_fast": True,
    "parallel_execution": False,  # Execução determinística
    "cache_enabled": False,  # Sempre reprocessar em testes
    "retry_on_error": False,
    "timeout_seconds": 5.0,  # Timeout baixo para testes rápidos
}


def merge_guardrail_config(
    base_config: GuardrailConfig, overrides: GuardrailConfig
) -> GuardrailConfig:
    """
    Faz merge de configurações de guardrail.

    Args:
        base_config: Configuração base
        overrides: Configurações para sobrescrever

    Returns:
        Nova configuração com overrides aplicados
    """
    merged: GuardrailConfig = {**base_config}
    merged.update(overrides)
    return merged


def get_guardrail_config_for_environment(env: str = "development") -> GuardrailConfig:
    """
    Retorna configuração apropriada para o ambiente.

    Args:
        env: Ambiente ("development", "production", "testing")

    Returns:
        Configuração apropriada para o ambiente
    """
    configs = {
        "development": DEVELOPMENT_GUARDRAIL_CONFIG,
        "production": PRODUCTION_GUARDRAIL_CONFIG,
        "testing": TESTING_GUARDRAIL_CONFIG,
    }

    return configs.get(env, DEFAULT_GUARDRAIL_CONFIG)
