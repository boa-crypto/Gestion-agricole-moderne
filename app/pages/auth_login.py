import reflex as rx
import reflex_enterprise as rxe
import os
from collections.abc import Sequence
from reflex_enterprise.auth import AuthUserState

_PROVIDER_NAME = os.environ.get("OIDC_PROVIDER_NAME", "")
_LOGIN_LABEL = (
    f"Continue with {_PROVIDER_NAME}" if _PROVIDER_NAME else "Sign in"
)


class LoginRedirectState(rx.State):
    @rxe.event(auth=False)
    def continue_to_app(self):
        raw = self.router.page.params.get("redirect_to", "/")
        target = (
            raw
            if isinstance(raw, str)
            and raw.startswith("/")
            and not raw.startswith("//")
            and not any(c in raw for c in "\t\r\n\\")
            else "/"
        )
        return rx.redirect(target)


def provider_button(provider) -> rx.Component:
    return provider.get_login_button(
        rx.el.button(
            _LOGIN_LABEL,
            class_name="w-full rounded-xl bg-lime-300 px-6 py-3 font-semibold text-[#04120c] hover:bg-lime-200 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-amber-300",
        ),
    )


def login_page(*, providers: Sequence, **context) -> rx.Component:
    return rx.fragment(
        rx.el.main(
            rx.el.section(
                rx.el.p(
                    "AgriPro",
                    class_name="text-sm font-semibold tracking-widest text-lime-300",
                ),
                rx.el.h1(
                    "Bienvenue",
                    class_name="mt-5 font-['Instrument_Serif'] text-5xl text-emerald-50",
                ),
                rx.el.p(
                    "Connectez-vous pour accéder à votre exploitation.",
                    class_name="mt-4 text-sm text-emerald-100",
                ),
                rx.el.div(
                    *map(provider_button, providers),
                    class_name="mt-8 flex flex-col gap-3",
                ),
                class_name="w-full max-w-md rounded-2xl border border-emerald-100/20 bg-[#081c13] p-8 sm:p-10",
            ),
            class_name="flex min-h-dvh w-full items-center justify-center bg-[#04120c] px-5 py-12 font-['Inter'] text-emerald-50",
        ),
        rx.cond(
            AuthUserState.provider_name != "",
            rx.el.div(on_mount=LoginRedirectState.continue_to_app),
        ),
    )
