"""Utilitaires partagés par les scripts de vérification métier.

Ces modules (`test_stock`, `test_expenses`, `test_guide`…) sont des scripts
autonomes hérités, antérieurs à l'adoption de pytest : chacun expose
`async def main()` et s'exécute par `python tests/test_xxx.py`. Ils importent
tous `run_event`, qui n'avait jamais été versionné.

`run_event` exécute un gestionnaire d'événement Reflex hors du contexte
navigateur : l'état est muté sur place, les deltas éventuellement produits sont
consommés puis ignorés. Les assertions des scripts portent donc directement sur
les attributs de l'instance d'état.
"""

from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable

import reflex as rx

# Les scripts hérités instancient les états directement (`StockState()`),
# ce que Reflex 0.10 refuse hors d'un contexte d'application. Le harnais de
# test rétablit donc l'ancien comportement, et lui seul.
_ORIGINAL_INIT = rx.State.__init__


def _testing_init(self: rx.State, *args: Any, **kwargs: Any) -> None:
    kwargs.setdefault("_reflex_internal_init", True)
    _ORIGINAL_INIT(self, *args, **kwargs)


if not getattr(rx.State, "_agripro_test_init", False):
    rx.State.__init__ = _testing_init  # type: ignore[method-assign]
    rx.State._agripro_test_init = True  # type: ignore[attr-defined]


async def run_event(
    handler: Callable[..., Any], *args: Any, **kwargs: Any
) -> Any:
    """Exécute un gestionnaire d'événement et retourne sa dernière valeur.

    - gestionnaire générateur asynchrone (`@rx.event` avec `yield`) : les
      deltas sont consommés jusqu'à épuisement ;
    - coroutine simple : elle est attendue ;
    - fonction synchrone : sa valeur de retour est renvoyée telle quelle.
    """
    result = handler(*args, **kwargs)

    if inspect.isasyncgen(result):
        last: Any = None
        async for item in result:
            last = item
        return last

    if inspect.isawaitable(result):
        return await result

    return result


async def run_events(*handlers: Awaitable[Any] | Callable[..., Any]) -> None:
    """Exécute plusieurs gestionnaires à la suite."""
    for handler in handlers:
        if callable(handler):
            await run_event(handler)
        else:  # coroutine déjà instanciée
            await handler
