import reflex as rx

from app.components.design import eyebrow
from app.components.menu_auth import login_panel
from app.components.menu_policy_admin import configuration_administration
from app.components.shell import app_shell
from app.states.menu_auth_state import MenuAuthState
from app.states.menu_configuration_state import MenuConfigurationState


def configuration_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            rx.el.header(
                eyebrow("Administration des accès", tone="accent"),
                rx.el.h1(
                    rx.el.span("Configuration & "),
                    rx.el.span("accès", class_name="ap-italic text-[#D8FA5E]"),
                    class_name="ap-display mt-5 text-[clamp(2.4rem,4.6vw,4.1rem)] text-[#f2efe4]",
                ),
                rx.el.p(
                    "Administrez les menus, les rôles et les comptes connectés. "
                    "Consultez les droits effectifs et le journal des modifications.",
                    class_name="mt-4 max-w-3xl text-[13px] leading-relaxed text-[#C9C5B4]/70",
                ),
                rx.el.p(
                    "Les refus sont prioritaires. La Configuration reste activée et "
                    "au moins un administrateur doit conserver son accès.",
                    class_name="mt-3 border-l-2 border-[#FF5A2B] pl-3 text-[12px] leading-relaxed text-[#FF8A5B]",
                ),
                class_name="w-full border-b border-[#F2EFE4]/12 pb-8",
            ),
            rx.cond(
                MenuConfigurationState.error != "",
                rx.el.div(
                    rx.el.p(
                        MenuConfigurationState.error,
                        role="alert",
                        class_name="text-sm text-[#ff9b8c]",
                    ),
                    rx.el.button(
                        "Réessayer",
                        on_click=MenuConfigurationState.load_configuration,
                        class_name="mt-2 rounded-none border border-[#f2efe4]/22 bg-[#14160f] px-3 py-2 text-sm text-[#d8fa5e] focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
                    ),
                    class_name="mt-5 rounded-none border border-[#ff9b8c]/25 bg-[#2a0d08]/20 p-4",
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
