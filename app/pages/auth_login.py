import reflex as rx
import reflex_enterprise as rxe
import os
from collections.abc import Sequence
from reflex_enterprise.auth import AuthUserState

from app.components.design import eyebrow, hairline

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
            class_name=(
                "ap-mono w-full border border-[rgb(var(--ap-accent-rgb))] bg-[rgb(var(--ap-accent-rgb))] px-6 py-3.5 "
                "text-[10px] uppercase tracking-[0.22em] text-[rgb(var(--ap-ink-rgb))] "
                "transition-colors hover:bg-[rgb(var(--ap-accent-soft-rgb))]"
            ),
        ),
    )


def login_page(*, providers: Sequence, **context) -> rx.Component:
    return rx.fragment(
        rx.el.main(
            rx.el.div(
                rx.el.div(
                    rx.el.span(class_name="h-2 w-2 bg-[rgb(var(--ap-accent-rgb))]"),
                    rx.el.span(
                        "AgriPro",
                        class_name="ap-serif text-2xl text-[rgb(var(--ap-paper-rgb))]",
                    ),
                    rx.el.span(
                        "Édition agronomique",
                        class_name=(
                            "ap-mono ml-4 hidden border-l border-[rgb(var(--ap-paper-rgb)/0.24)] pl-4 "
                            "text-[9px] uppercase tracking-[0.26em] text-[rgb(var(--ap-paper-muted-rgb)/0.86)] sm:block"
                        ),
                    ),
                    class_name="flex items-center",
                ),
                rx.el.div(
                    eyebrow("Accès partenaire", tone="accent", class_name="mt-16"),
                    rx.el.h1(
                        rx.el.span("Bienvenue dans "),
                        rx.el.span("l'édition", class_name="ap-italic text-[rgb(var(--ap-accent-rgb))]"),
                        class_name="ap-display mt-6 text-[clamp(2.6rem,5vw,4rem)] text-[rgb(var(--ap-paper-rgb))]",
                    ),
                    rx.el.p(
                        "Identifiez-vous pour ouvrir votre exploitation, ses "
                        "parcelles et ses registres.",
                        class_name="mt-5 max-w-md text-[13px] leading-relaxed text-[rgb(var(--ap-paper-muted-rgb)/0.90)]",
                    ),
                    rx.el.div(
                        *map(provider_button, providers),
                        class_name="mt-10 flex w-full max-w-md flex-col gap-3",
                    ),
                    class_name="mt-10 w-full max-w-md",
                ),
                rx.el.div(
                    hairline(),
                    rx.el.p(
                        "Session vérifiée avant tout chargement métier",
                        class_name=(
                            "ap-mono pt-5 text-[9px] uppercase tracking-[0.24em] "
                            "text-[rgb(var(--ap-paper-muted-rgb)/0.82)]"
                        ),
                    ),
                    class_name="mt-16 w-full max-w-md",
                ),
                class_name="flex min-h-dvh w-full max-w-md flex-col justify-center px-6 py-14",
            ),
            rx.el.aside(
                eyebrow("Numéro MMXXVI — Pilotage végétal", tone="accent"),
                rx.el.p(
                    rx.el.span("La terre,\n"),
                    rx.el.span("tenue comme "),
                    rx.el.span("un livre.", class_name="ap-italic text-[rgb(var(--ap-accent-rgb))]"),
                    class_name=(
                        "ap-display mt-8 whitespace-pre-line "
                        "text-[clamp(2.6rem,4.4vw,4.4rem)] text-[rgb(var(--ap-paper-rgb))]"
                    ),
                ),
                class_name=(
                    "hidden w-[46%] shrink-0 flex-col justify-center border-l "
                    "border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb))] p-10 lg:flex xl:p-14"
                ),
            ),
            class_name=(
                "flex min-h-dvh w-full items-stretch justify-center bg-[rgb(var(--ap-ink-rgb))] "
                "font-['Inter_Tight'] text-[rgb(var(--ap-paper-rgb))] antialiased"
            ),
        ),
        rx.cond(
            AuthUserState.provider_name != "",
            rx.el.div(on_mount=LoginRedirectState.continue_to_app),
        ),
    )
