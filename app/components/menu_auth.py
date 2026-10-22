import reflex as rx

from app.states.menu_auth_state import MenuAuthState


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
                href="/configuration",
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
            "Le premier compte créé devient administrateur des menus. Les comptes suivants sont lecteurs.",
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
        rx.el.button(
            rx.cond(
                MenuAuthState.signup,
                "Déjà inscrit ? Se connecter",
                "Pas encore de compte ? S’inscrire",
            ),
            type="button",
            on_click=MenuAuthState.change_mode,
            disabled=MenuAuthState.busy,
            class_name="mt-5 rounded-lg py-2 text-sm text-lime-300 focus-visible:outline-2 focus-visible:outline-lime-300",
        ),
        class_name="w-full max-w-xl rounded-3xl border border-lime-300/20 bg-[#071c13] p-6 sm:p-8",
    )
