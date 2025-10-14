from typing import Never


def raise_error(message: str, error_type: type[Exception] = Exception) -> Never:
    raise error_type(message)
