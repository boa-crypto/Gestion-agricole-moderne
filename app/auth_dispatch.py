import reflex as rx

import inspect
from functools import wraps
from typing import Callable
from urllib.parse import parse_qs, urlencode, urlsplit

from app.navigation import ROUTE_MATRIX


REGISTERED_ROUTES = frozenset(entry["route"] for entry in ROUTE_MATRIX.values())
PAGE_LOADERS: dict[str, tuple[rx.event.EventHandler, ...]] = {}


def safe_destination(value: str) -> str:
    if (
        not value
        or len(value) > 2048
        or "\\" in value
        or any(ord(c) < 32 for c in value)
    ):
        return "/"
    url = urlsplit(value)
    if url.scheme or url.netloc or url.path not in REGISTERED_ROUTES:
        return "/"
    query = parse_qs(url.query)
    allowed = {
        key: query[key][0] for key in ("cockpit", "vue") if query.get(key)
    }
    destination = url.path
    if allowed:
        destination = f"{destination}?{urlencode(allowed)}"
    if (
        url.fragment
        and url.fragment.replace("-", "").replace("_", "").isalnum()
    ):
        destination = f"{destination}#{url.fragment}"
    return destination


async def _ticket(state, key: str) -> tuple[str, int, int] | None:
    from app.states.menu_auth_state import MenuAuthState

    auth = await state.get_state(MenuAuthState)
    if (
        not auth.ready
        or not auth.authenticated
        or auth._verified_token != auth.token
        or not auth.page_allowed
    ):
        return None
    if auth._pending_loader == key:
        auth._pending_loader = ""
        return auth._dispatch_page, auth._dispatch_index, auth._generation
    return "", -1, auth._generation


async def _run_implementation(implementation: Callable, state):
    result = implementation(state)
    if inspect.isasyncgen(result):
        async for event in result:
            yield event
    elif inspect.isawaitable(result):
        event = await result
        if event is not None:
            yield event
    elif result is not None:
        yield result


def register_loaders(page: str, *handlers: rx.event.EventHandler) -> None:
    PAGE_LOADERS[page] = handlers
    for handler in handlers:
        if getattr(handler.fn, "_agripro_guarded", False):
            continue
        implementation = inspect.unwrap(handler.fn)
        key = f"{implementation.__module__}.{implementation.__qualname__}"
        background = handler.is_background

        def build_wrapper(implementation, key, background):
            @wraps(implementation)
            async def guarded(state):
                from app.states.menu_auth_state import MenuAuthState

                if background:
                    async with state:
                        ticket = await _ticket(state, key)
                else:
                    ticket = await _ticket(state, key)
                if ticket is None:
                    return
                async for event in _run_implementation(implementation, state):
                    yield event
                page_key, index, generation = ticket
                if index >= 0:
                    yield MenuAuthState.dispatch_loader(
                        page_key, index + 1, generation
                    )

            guarded._agripro_guarded = True
            return guarded

        object.__setattr__(
            handler, "fn", build_wrapper(implementation, key, background)
        )


def loader_key(handler: rx.event.EventHandler) -> str:
    implementation = inspect.unwrap(handler.fn)
    return f"{implementation.__module__}.{implementation.__qualname__}"
