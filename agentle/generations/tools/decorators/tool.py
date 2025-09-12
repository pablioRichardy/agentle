from collections.abc import Awaitable, Callable

from agentle.generations.tools.tool import Tool


def tool[**P, R](
    func: Callable[P, R] | Callable[P, Awaitable[R]],
    before_call: Callable[P, R] | Callable[P, Awaitable[R]] | None = None,
    after_call: Callable[P, R] | Callable[P, Awaitable[R]] | None = None,
) -> Tool[P, R]:
    return Tool[P, R].from_callable(
        func,
        before_call=before_call,
        after_call=after_call,
    )
