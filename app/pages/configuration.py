import reflex as rx

from app.components.design import (
    action_button,
    eyebrow,
    meta_ledger,
    meta_row,
    page_hero,
    refresh_button,
)
from app.components.menu_auth import login_panel
from app.components.menu_policy_admin import configuration_administration
from app.components.shell import app_shell
from app.states.menu_auth_state import MenuAuthState
from app.states.menu_configuration_state import MenuConfigurationState


def configuration_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            page_hero(
                "Administration des accès",
                rx.el.span(
                    rx.el.span("Configuration & "),
                    rx.el.span("accès", class_name="ap-italic text-[#D8FA5E]"),
                ),
                "Administrez les menus, les rôles et les comptes connectés. "
                "Consultez les droits effectifs et le journal des modifications.",
                meta=meta_ledger(
                    meta_row("Session", MenuAuthState.email),
                    meta_row("Périmètre", "Menus · rôles · comptes", tone="muted"),
                ),
                actions=rx.el.div(
                    refresh_button(
                        on_click=MenuConfigurationState.load_configuration,
                        loading=MenuConfigurationState.loading,
                        label="Recharger",
                    ),
                    class_name="flex flex-wrap items-center gap-2",
                ),
            ),
            rx.el.p(
                "Les refus sont prioritaires. La Configuration reste activée et "
                "au moins un administrateur doit conserver son accès.",
                class_name=(
                    "mt-5 border-l-2 border-[#FF5A2B] pl-3 text-[12px] "
                    "leading-relaxed text-[#FF8A5B]"
                ),
            ),
            rx.cond(
                MenuConfigurationState.error != "",
                rx.el.div(
                    rx.icon(
                        "octagon-alert",
                        class_name="h-4 w-4 shrink-0 text-[#FF8A5B]",
                    ),
                    rx.el.div(
                        rx.el.p(
                            MenuConfigurationState.error,
                            role="alert",
                            class_name="text-sm text-[#FFBCB0]",
                        ),
                        action_button(
                            "Réessayer",
                            icon="rotate-ccw",
                            tone="outline",
                            on_click=MenuConfigurationState.load_configuration,
                            class_name="mt-3",
                        ),
                        class_name="min-w-0",
                    ),
                    class_name=(
                        "flex items-start gap-3 border-l-2 border-[#FF5A2B] "
                        "bg-[#FF5A2B]/[0.06] px-4 py-4 mt-6"
                    ),
                ),
                rx.fragment(),
            ),
            rx.el.div(
                rx.cond(
                    (~MenuAuthState.ready) | MenuConfigurationState.loading,
                    rx.el.div(
                        rx.el.p(
                            "Chargement de la session et de la configuration…",
                            role="status",
                            class_name="text-sm text-[#c9c5b4]",
                        ),
                        rx.el.div(
                            class_name="mt-4 h-40 w-full animate-pulse rounded-none bg-[#1a1e14]/40"
                        ),
                        class_name="w-full",
                    ),
                    rx.cond(
                        MenuAuthState.authenticated,
                        rx.cond(
                            MenuConfigurationState.allowed,
                            configuration_administration(),
                            rx.el.section(
                                rx.icon(
                                    "shield",
                                    class_name="h-8 w-8 text-[#ff8a5b]",
                                ),
                                rx.el.h2(
                                    "Accès réservé à l’administrateur",
                                    class_name="mt-3 ap-serif text-3xl text-[#f2efe4]",
                                ),
                                rx.el.p(
                                    "Votre session est valide, mais les droits de configuration requis ne sont pas accordés à votre compte.",
                                    class_name="mt-3 text-sm text-[#c9c5b4]/80",
                                ),
                                class_name="w-full rounded-none border border-[#ff8a5b]/20 bg-[#14160F] p-6",
                            ),
                        ),
                        login_panel(),
                    ),
                ),
                class_name="mt-8 w-full",
            ),
            class_name="flex w-full flex-col gap-6",
        ),
        "configuration",
    )
