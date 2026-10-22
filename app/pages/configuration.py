import reflex as rx

from app.components.menu_auth import login_panel
from app.components.menu_configuration import menu_configuration_panel
from app.components.side_rail import side_rail
from app.states.menu_auth_state import MenuAuthState
from app.states.menu_configuration_state import MenuConfigurationState


def configuration_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            side_rail("configuration"),
            rx.el.h1(
                "Configuration des menus",
                class_name="font-['Instrument_Serif'] text-4xl sm:text-5xl text-emerald-50",
            ),
            rx.el.p(
                "Personnalisez les cockpits et leurs sous-menus. Les routes directes et les permissions métier restent inchangées.",
                class_name="mt-3 text-sm text-emerald-100/80",
            ),
            rx.el.p(
                "Désactiver un cockpit masque ses enfants sans modifier leurs réglages. La Configuration reste toujours activée.",
                class_name="mt-2 text-sm text-amber-200",
            ),
            rx.cond(
                MenuConfigurationState.error != "",
                rx.el.div(
                    rx.el.p(
                        MenuConfigurationState.error,
                        role="alert",
                        class_name="text-sm text-red-300",
                    ),
                    rx.el.button(
                        "Réessayer",
                        on_click=MenuConfigurationState.load_configuration,
                        class_name="mt-2 rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-lime-300 focus-visible:outline-2 focus-visible:outline-lime-300",
                    ),
                    class_name="mt-5 rounded-2xl border border-red-300/25 bg-red-950/20 p-4",
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
                            class_name="text-sm text-emerald-100",
                        ),
                        rx.el.div(
                            class_name="mt-4 h-40 w-full animate-pulse rounded-2xl bg-emerald-900/40"
                        ),
                        class_name="w-full",
                    ),
                    rx.cond(
                        MenuAuthState.authenticated,
                        rx.cond(
                            MenuConfigurationState.allowed,
                            menu_configuration_panel(),
                            rx.el.section(
                                rx.icon(
                                    "shield",
                                    class_name="h-8 w-8 text-amber-300",
                                ),
                                rx.el.h2(
                                    "Accès réservé à l’administrateur",
                                    class_name="mt-3 font-['Instrument_Serif'] text-3xl text-emerald-50",
                                ),
                                rx.el.p(
                                    "Votre compte lecteur ne peut ni consulter ni modifier les réglages des menus.",
                                    class_name="mt-3 text-sm text-emerald-100/80",
                                ),
                                class_name="w-full rounded-2xl border border-amber-300/20 bg-[#071c13] p-6",
                            ),
                        ),
                        login_panel(),
                    ),
                ),
                class_name="mt-8 w-full",
            ),
            class_name="relative w-full max-w-[110rem] mx-auto px-4 sm:px-8 md:pl-24 lg:pl-28 xl:pl-72 py-10 pb-28 md:pb-10",
        ),
        class_name="min-h-screen w-full bg-[#04120c] font-['Inter'] text-emerald-50 antialiased",
    )
