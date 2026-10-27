import reflex as rx

from app.states.menu_auth_state import MenuAuthState
from app.states.navigation_state import NavigationState


def account_controls() -> rx.Component:
    return rx.el.div(
        rx.cond(
            MenuAuthState.authenticated,
            rx.el.div(
                rx.el.span(
                    MenuAuthState.email,
                    class_name="hidden lg:inline max-w-48 truncate text-xs text-emerald-100",
                ),
                rx.el.button(
                    "Déconnexion",
                    on_click=MenuAuthState.logout,
                    disabled=MenuAuthState.busy,
                    class_name="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-lime-300 focus-visible:outline-2 focus-visible:outline-lime-300 disabled:opacity-50",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.a(
                "Connexion",
                href="/",
                class_name="rounded-xl border border-lime-300/25 bg-lime-300/10 px-3 py-2 text-xs text-lime-200 focus-visible:outline-2 focus-visible:outline-lime-300",
            ),
        ),
        class_name="shrink-0",
    )


def login_panel() -> rx.Component:
    return rx.el.section(
        rx.el.h2(
            rx.cond(
                MenuAuthState.signup,
                "Créer votre compte",
                "Connexion à AgriPro",
            ),
            class_name="font-['Instrument_Serif'] text-3xl text-emerald-50",
        ),
        rx.el.p(
            "Connectez-vous pour accéder à votre exploitation. La session est vérifiée avant tout chargement métier.",
            class_name="mt-3 text-sm text-emerald-100/80",
        ),
        rx.el.form(
            rx.el.label(
                "Adresse e-mail",
                html_for="auth-email",
                class_name="block text-sm text-emerald-100",
            ),
            rx.el.input(
                id="auth-email",
                name="email",
                type="email",
                required=True,
                max_length=320,
                auto_complete="email",
                placeholder="vous@exemple.fr",
                class_name="mt-2 w-full rounded-xl border border-white/20 bg-[#04120c] px-4 py-3 text-emerald-50 focus-visible:outline-2 focus-visible:outline-lime-300",
            ),
            rx.el.label(
                "Mot de passe",
                html_for="auth-password",
                class_name="mt-5 block text-sm text-emerald-100",
            ),
            rx.el.input(
                id="auth-password",
                name="password",
                type="password",
                required=True,
                min_length=12,
                max_length=256,
                auto_complete=rx.cond(
                    MenuAuthState.signup, "new-password", "current-password"
                ),
                aria_describedby="auth-password-help",
                class_name="mt-2 w-full rounded-xl border border-white/20 bg-[#04120c] px-4 py-3 text-emerald-50 focus-visible:outline-2 focus-visible:outline-lime-300",
            ),
            rx.el.p(
                "12 à 256 caractères. Utilisez un mot de passe unique.",
                id="auth-password-help",
                class_name="mt-2 text-xs text-emerald-100/70",
            ),
            rx.cond(
                MenuAuthState.error != "",
                rx.el.p(
                    MenuAuthState.error,
                    role="alert",
                    class_name="mt-4 text-sm text-red-300",
                ),
                rx.fragment(),
            ),
            rx.el.button(
                rx.cond(
                    MenuAuthState.busy,
                    "Veuillez patienter…",
                    rx.cond(
                        MenuAuthState.signup, "Créer un compte", "Se connecter"
                    ),
                ),
                type="submit",
                disabled=MenuAuthState.busy,
                class_name="mt-5 w-full rounded-xl bg-[#a3e635] px-4 py-3 font-semibold text-[#04120c] hover:bg-lime-300 focus-visible:outline-2 focus-visible:outline-amber-300 disabled:opacity-50",
            ),
            on_submit=MenuAuthState.submit,
            reset_on_submit=True,
            class_name="mt-6",
        ),
        rx.cond(
            MenuAuthState.signup,
            rx.el.button(
                "Déjà inscrit ? Se connecter",
                type="button",
                on_click=MenuAuthState.change_mode,
                disabled=MenuAuthState.busy,
                class_name="mt-5 rounded-lg px-2 py-3 text-sm text-lime-300 hover:text-lime-200 focus-visible:outline-2 focus-visible:outline-lime-300 disabled:opacity-50",
            ),
            rx.el.div(
                rx.el.p(
                    "Première visite ? Créez votre compte pour accéder à AgriPro.",
                    id="auth-first-visit",
                    class_name="text-sm leading-relaxed text-emerald-100",
                ),
                rx.el.button(
                    rx.icon(
                        "user-plus", class_name="h-5 w-5", aria_hidden=True
                    ),
                    "Créer mon compte",
                    type="button",
                    on_click=MenuAuthState.change_mode,
                    disabled=MenuAuthState.busy,
                    aria_describedby="auth-first-visit",
                    class_name="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-[#a3e635] bg-[#a3e635]/10 px-4 py-3 font-semibold text-[#a3e635] hover:bg-[#a3e635]/20 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-300 disabled:opacity-50",
                ),
                class_name="mt-6 border-t border-lime-300/20 pt-5",
            ),
        ),
        class_name="w-full max-w-xl rounded-3xl border border-lime-300/20 bg-[#071c13] p-6 sm:p-8",
    )


def authentication_shell() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.div(
                rx.icon("leaf", class_name="h-8 w-8 text-[#a3e635]"),
                rx.el.h1(
                    "AgriPro",
                    class_name="font-['Instrument_Serif'] text-5xl text-emerald-50",
                ),
                class_name="mb-8 flex items-center justify-center gap-3",
            ),
            rx.cond(
                ~MenuAuthState.ready,
                rx.el.section(
                    rx.el.p(
                        "Vérification de votre session…",
                        role="status",
                        class_name="text-emerald-100 text-base",
                    ),
                    rx.el.div(
                        class_name="mt-5 h-2 w-full animate-pulse rounded-full bg-[#a3e635]/30"
                    ),
                    class_name="w-full max-w-xl rounded-3xl border border-lime-300/20 bg-[#071c13] p-8",
                ),
                rx.cond(
                    (MenuAuthState.error != "") & (MenuAuthState.token != ""),
                    rx.el.section(
                        rx.el.h2(
                            "Vérification indisponible",
                            class_name="font-['Instrument_Serif'] text-3xl text-emerald-50",
                        ),
                        rx.el.p(
                            MenuAuthState.error,
                            role="alert",
                            class_name="mt-4 text-sm text-amber-200",
                        ),
                        rx.el.button(
                            "Réessayer",
                            on_click=MenuAuthState.retry_page,
                            class_name="mt-6 rounded-xl bg-[#a3e635] px-4 py-3 font-semibold text-[#04120c] focus-visible:outline-2 focus-visible:outline-amber-300",
                        ),
                        rx.el.button(
                            "Déconnexion",
                            on_click=MenuAuthState.logout,
                            disabled=MenuAuthState.busy,
                            class_name="ml-3 mt-6 rounded-xl border border-white/20 bg-white/5 px-4 py-3 text-emerald-50 focus-visible:outline-2 focus-visible:outline-lime-300 disabled:opacity-50",
                        ),
                        class_name="w-full max-w-xl rounded-3xl border border-amber-300/25 bg-[#071c13] p-8",
                    ),
                    login_panel(),
                ),
            ),
            class_name="mx-auto flex w-full max-w-2xl flex-col items-center px-4 py-12 sm:py-20",
        ),
        class_name="min-h-dvh w-full bg-[#04120c] font-['Inter'] text-emerald-50 antialiased",
    )


def no_module_panel() -> rx.Component:
    return rx.el.main(
        rx.el.section(
            rx.icon("leaf", class_name="h-9 w-9 text-[#a3e635]"),
            rx.el.h1(
                "AgriPro",
                class_name="mt-4 font-['Instrument_Serif'] text-4xl text-emerald-50",
            ),
            rx.el.h2(
                rx.cond(
                    MenuAuthState.has_modules,
                    "Destination non accessible",
                    "Aucun module accessible",
                ),
                class_name="mt-6 text-xl font-semibold text-emerald-50",
            ),
            rx.el.p(
                rx.cond(
                    MenuAuthState.has_modules,
                    "Cette destination n’est pas disponible avec vos droits actuels. Choisissez un accès autorisé ci-dessous.",
                    "Votre compte est connecté, mais aucun module n’est activé pour vous. Contactez le responsable des accès de votre exploitation.",
                ),
                role="status",
                class_name="mt-3 text-sm text-emerald-100/80",
            ),
            rx.el.nav(
                rx.foreach(
                    NavigationState.visible_navigation,
                    lambda entry: rx.el.a(
                        rx.icon(
                            entry["icon"], class_name="h-4 w-4 text-lime-300"
                        ),
                        entry["label"],
                        href=entry["href"],
                        class_name="flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-emerald-50 focus-visible:outline-2 focus-visible:outline-lime-300 hover:border-lime-300/40",
                    ),
                ),
                aria_label="Destinations autorisées",
                class_name="mt-6 flex flex-col gap-2",
            ),
            rx.el.button(
                "Vérifier à nouveau mes accès",
                on_click=MenuAuthState.retry_page,
                class_name="mt-6 rounded-xl bg-[#a3e635] px-4 py-3 font-semibold text-[#04120c] focus-visible:outline-2 focus-visible:outline-amber-300",
            ),
            rx.el.div(account_controls(), class_name="mt-5"),
            class_name="mx-auto w-full max-w-2xl rounded-3xl border border-lime-300/20 bg-[#071c13] p-6 sm:p-10",
        ),
        class_name="min-h-dvh w-full bg-[#04120c] px-4 py-12 font-['Inter'] text-emerald-50",
    )


def guarded_page(content: rx.Component, route: str) -> rx.Component:
    return rx.cond(
        MenuAuthState.ready
        & MenuAuthState.authenticated
        & (MenuAuthState.verified_path == route)
        & (MenuAuthState.router.url.path == route),
        rx.cond(MenuAuthState.page_allowed, content, no_module_panel()),
        authentication_shell(),
    )
