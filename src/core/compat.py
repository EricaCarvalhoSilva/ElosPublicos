"""
Compatibilidade do decorador @override.

O decorador `typing.override` (Python 3.12+) é o equivalente em Python ao
@Override do Java: marca explicitamente que um método sobrescreve outro da
classe-mãe. Em versões anteriores do Python, usamos um decorador neutro.
"""
try:
    from typing import override
except ImportError:  # Python < 3.12
    from typing import Callable, TypeVar

    _F = TypeVar("_F", bound=Callable)

    def override(func: _F) -> _F:  # type: ignore[no-redef]
        return func

__all__ = ["override"]
