import reflex as rx

from app.components.design import eyebrow, hairline
from app.states.menu_auth_state import MenuAuthState
from app.states.navigation_state import NavigationState


def account_controls() -> rx.Component:
    """Contrôles de session du masthead, en registre mono éditorial."""
    return rx.el.div(
        rx.cond(
            MenuAuthState.authenticated,
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        "Session",
                        class_name="ap-mono text-[8px] uppercase tracking-[0.24em] text-[#C9C5B4]/35",
                    ),
                    rx.el.span(
                        MenuAuthState.email,
                        class_name="ap-mono max-w-[12rem] truncate text-[9px] tracking-[0.04em] text-[#C9C5B4]/80",
                    ),
                    class_name="hidden flex-col gap-0.5 xl:flex",
                ),
                rx.el.button(
                    rx.icon("log-out", class_name="h-4 w-4 sm:hidden"),
                    rx.el.span(
                        "Déconnexion", class_name="hidden sm:inline"
                    ),
                    type="button",
                    on_click=MenuAuthState.logout,
                    disabled=MenuAuthState.busy,
                    aria_label="Déconnexion",
                    title="Déconnexion",
                    class_name=(
                        "ap-mono inline-flex h-9 w-9 items-center justify-center "
                        "border border-[#F2EFE4]/16 text-[9px] uppercase "
                        "tracking-[0.18em] text-[#C9C5B4] transition-colors "
                        "hover:border-[#FF5A2B]/60 hover:text-[#FF8A5B] "
                        "disabled:opacity-40 sm:w-auto sm:px-3"
                    ),
                ),
                class_name="flex items-center gap-3",
            ),
            rx.el.a(
                "Connexion",
                href="/",
                class_name=(
                    "ap-mono inline-flex h-9 items-center border border-[#D8FA5E]/40 "
                    "bg-[#D8FA5E]/10 px-3 text-[9px] uppercase tracking-[0.18em] "
                    "text-[#D8FA5E] transition-colors hover:bg-[#D8FA5E]/20"
                ),
            ),
        ),
        class_name="shrink-0",
    )


def _field(label: str, control: rx.Component, html_for: str) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=html_for,
            class_name="ap-mono mb-2 block text-[9px] uppercase tracking-[0.24em] text-[#C9C5B4]/50",
        ),
        control,
        class_name="w-full",
    )


def login_panel() -> rx.Component:
    input_class = (
        "w-full border border-[#F2EFE4]/18 bg-[#101208] px-4 py-3.5 "
        "text-[15px] text-[#F2EFE4] placeholder:text-[#C9C5B4]/25 "
        "transition-colors hover:border-[#F2EFE4]/30 focus:border-[#D8FA5E] "
        "focus:outline-none"
    )
    return rx.el.section(
        eyebrow("Accès sécurisé", tone="accent"),
        rx.el.h2(
            rx.cond(
                MenuAuthState.signup,
                rx.fragment(
                    "Créer votre ",
                    rx.el.span("compte", class_name="ap-italic text-[#D8FA5E]"),
                ),
                rx.fragment(
                    "Entrer dans ",
                    rx.el.span("l'édition", class_name="ap-italic text-[#D8FA5E]"),
                ),
            ),
            class_name="ap-display mt-5 text-[clamp(2.2rem,4vw,3.4rem)] text-[#F2EFE4]",
        ),
        rx.el.p(
            "Votre exploitation, vos registres et vos campagnes dans une seule "
            "lecture. La session et les droits sont vérifiés avant tout "
            "chargement métier.",
            class_name="mt-4 max-w-sm text-[13px] leading-relaxed text-[#C9C5B4]/70",
        ),
        rx.el.form(
            _field(
                "Adresse e-mail",
                rx.el.input(
                    id="auth-email",
                    name="email",
                    type="email",
                    required=True,
                    max_length=320,
                    auto_complete="email",
                    placeholder="vous@exemple.fr",
                    class_name=input_class,
                ),
                "auth-email",
            ),
            _field(
                "Mot de passe",
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
                    class_name=input_class,
                ),
                "auth-password",
            ),
            rx.el.p(
                "12 à 256 caractères. Utilisez un mot de passe unique.",
                id="auth-password-help",
                class_name="ap-mono mt-2 text-[9px] uppercase tracking-[0.14em] text-[#C9C5B4]/35",
            ),
            rx.cond(
                MenuAuthState.error != "",
                rx.el.p(
                    MenuAuthState.error,
                    role="alert",
                    class_name=(
                        "mt-5 border-l-2 border-[#FF5A2B] bg-[#FF5A2B]/8 px-3 py-2 "
                        "text-[12px] leading-relaxed text-[#FFB894]"
                    ),
                ),
                rx.fragment(),
            ),
            rx.el.button(
                rx.cond(
                    MenuAuthState.busy,
                    "Veuillez patienter…",
                    rx.cond(
                        MenuAuthState.signup, "Créer mon compte", "Se connecter"
                    ),
                ),
                rx.icon(
                    "arrow-right",
                    class_name="h-4 w-4 transition-transform group-hover:translate-x-1",
                ),
                type="submit",
                disabled=MenuAuthState.busy,
                class_name=(
                    "group mt-7 flex w-full items-center justify-between border "
                    "border-[#D8FA5E] bg-[#D8FA5E] px-5 py-3.5 ap-mono text-[10px] "
                    "uppercase tracking-[0.22em] text-[#0A0A08] transition-colors "
                    "hover:bg-[#E4FF9B] disabled:opacity-50"
                ),
            ),
            on_submit=MenuAuthState.submit,
            reset_on_submit=True,
            class_name="mt-9 flex w-full flex-col gap-5",
        ),
        rx.cond(
            MenuAuthState.signup,
            rx.el.button(
                "Déjà inscrit ? Se connecter",
                type="button",
                on_click=MenuAuthState.change_mode,
                disabled=MenuAuthState.busy,
                class_name=(
                    "ap-mono mt-6 text-[9px] uppercase tracking-[0.18em] "
                    "text-[#D8FA5E] underline decoration-[#D8FA5E]/30 underline-offset-4 "
                    "hover:decoration-[#D8FA5E] disabled:opacity-50"
                ),
            ),
            rx.el.div(
                rx.el.p(
                    "Première visite ? Ouvrez votre compte d'exploitation.",
                    id="auth-first-visit",
                    class_name="text-[12px] leading-relaxed text-[#C9C5B4]/55",
                ),
                rx.el.button(
                    rx.icon("user-plus", class_name="h-3.5 w-3.5", aria_hidden=True),
                    rx.el.span("Créer mon compte"),
                    type="button",
                    on_click=MenuAuthState.change_mode,
                    disabled=MenuAuthState.busy,
                    aria_describedby="auth-first-visit",
                    class_name=(
                        "ap-mono mt-3 inline-flex w-full items-center justify-center "
                        "gap-2 border border-[#F2EFE4]/18 px-4 py-3 text-[9px] "
                        "uppercase tracking-[0.18em] text-[#F2EFE4] transition-colors "
                        "hover:border-[#D8FA5E] hover:text-[#D8FA5E]"
                    ),
                ),
                class_name="mt-8 border-t border-[#F2EFE4]/12 pt-6",
            ),
        ),
        class_name="w-full max-w-md",
    )


def _cover() -> rx.Component:
    """Planche de couverture : manifeste typographique de la maison AgriPro."""
    return rx.el.aside(
        rx.el.div(
            rx.el.span(class_name="h-2 w-2 bg-[#D8FA5E]"),
            rx.el.span(
                "AgriPro",
                class_name="ap-serif text-2xl text-[#F2EFE4]",
            ),
            rx.el.span(
                "Édition agronomique",
                class_name=(
                    "ap-mono ml-4 border-l border-[#F2EFE4]/16 pl-4 text-[9px] "
                    "uppercase tracking-[0.26em] text-[#C9C5B4]/40"
                ),
            ),
            class_name="flex items-center",
        ),
        rx.el.div(
            eyebrow("Numéro MMXXVI — Pilotage végétal", tone="accent"),
            rx.el.p(
                rx.el.span("La terre,\n"),
                rx.el.span("tenue comme "),
                rx.el.span("un livre.", class_name="ap-italic text-[#D8FA5E]"),
                class_name=(
                    "ap-display mt-8 whitespace-pre-line text-[clamp(2.6rem,4.4vw,4.4rem)] "
                    "text-[#F2EFE4]"
                ),
            ),
            rx.el.p(
                "Parcelles, cultures, chantiers, troupeaux et comptes : chaque "
                "donnée trouve sa page, sa cote et sa lecture.",
                class_name="mt-8 max-w-sm text-[13px] leading-relaxed text-[#C9C5B4]/60",
            ),
            class_name="mt-16",
        ),
        rx.el.div(
            hairline(),
            rx.el.div(
                rx.el.span(
                    "Pilotage végétal",
                    class_name="ap-mono text-[9px] uppercase tracking-[0.24em] text-[#C9C5B4]/45",
                ),
                rx.el.span(
                    "Session vérifiée",
                    class_name="ap-mono text-[9px] uppercase tracking-[0.24em] text-[#C9C5B4]/45",
                ),
                rx.el.span(
                    "MMXXVI",
                    class_name="ap-mono text-[9px] uppercase tracking-[0.24em] text-[#C9C5B4]/45",
                ),
                class_name="flex items-center justify-between gap-4 pt-5",
            ),
            class_name="mt-auto",
        ),
        class_name=(
            "relative hidden w-[46%] shrink-0 flex-col justify-between border-r "
            "border-[#F2EFE4]/12 bg-[#0D0F09] p-10 lg:flex xl:p-14"
        ),
    )


def _session_check() -> rx.Component:
    return rx.el.section(
        rx.el.p(
            "Vérification de votre session…",
            role="status",
            class_name="ap-mono text-[10px] uppercase tracking-[0.22em] text-[#C9C5B4]/60",
        ),
        rx.el.div(
            class_name="mt-5 h-px w-full overflow-hidden bg-[#F2EFE4]/12",
        ),
        rx.el.div(
            class_name="mt-5 h-px w-1/3 animate-pulse bg-[#D8FA5E]",
        ),
        class_name="w-full max-w-md",
    )


def authentication_shell() -> rx.Component:
    return rx.el.main(
        _cover(),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.span(class_name="h-2 w-2 bg-[#D8FA5E]"),
                    rx.el.span(
                        "AgriPro",
                        class_name="ap-serif text-2xl text-[#F2EFE4]",
                    ),
                    class_name="mb-12 flex items-center gap-3 lg:hidden",
                ),
                rx.cond(
                    ~MenuAuthState.ready,
                    _session_check(),
                    rx.cond(
                        (MenuAuthState.error != "") & (MenuAuthState.token != ""),
                        rx.el.section(
                            eyebrow("Session interrompue", tone="flame"),
                            rx.el.h2(
                                "Vérification indisponible",
                                class_name="ap-display mt-5 text-4xl text-[#F2EFE4]",
                            ),
                            rx.el.p(
                                MenuAuthState.error,
                                role="alert",
                                class_name="mt-4 text-[13px] leading-relaxed text-[#FFB894]",
                            ),
                            rx.el.div(
                                rx.el.button(
                                    "Réessayer",
                                    type="button",
                                    on_click=MenuAuthState.retry_page,
                                    class_name=(
                                        "ap-mono border border-[#D8FA5E] bg-[#D8FA5E] px-4 py-3 "
                                        "text-[9px] uppercase tracking-[0.18em] text-[#0A0A08]"
                                    ),
                                ),
                                rx.el.button(
                                    "Déconnexion",
                                    type="button",
                                    on_click=MenuAuthState.logout,
                                    disabled=MenuAuthState.busy,
                                    class_name=(
                                        "ap-mono border border-[#F2EFE4]/18 px-4 py-3 "
                                        "text-[9px] uppercase tracking-[0.18em] text-[#F2EFE4] "
                                        "disabled:opacity-50"
                                    ),
                                ),
                                class_name="mt-7 flex flex-wrap items-center gap-3",
                            ),
                            class_name="w-full max-w-md",
                        ),
                        login_panel(),
                    ),
                ),
                class_name="flex w-full flex-col items-start",
            ),
            class_name=(
                "flex min-h-dvh w-full items-center justify-center px-6 py-14 "
                "sm:px-10 lg:w-[54%]"
            ),
        ),
        class_name=(
            "flex min-h-dvh w-full bg-[#0A0A08] font-['Inter_Tight'] text-[#F2EFE4] antialiased"
        ),
    )


def no_module_panel() -> rx.Component:
    return rx.el.main(
        rx.el.section(
            rx.el.div(
                rx.el.span(class_name="h-2 w-2 bg-[#FF5A2B]"),
                rx.el.span(
                    "AgriPro",
                    class_name="ap-serif text-2xl text-[#F2EFE4]",
                ),
                class_name="flex items-center gap-3",
            ),
            eyebrow("Droits effectifs", tone="flame", class_name="mt-12"),
            rx.el.h2(
                rx.cond(
                    MenuAuthState.has_modules,
                    "Destination non accessible",
                    "Aucun module accessible",
                ),
                class_name="ap-display mt-5 text-4xl text-[#F2EFE4]",
            ),
            rx.el.p(
                rx.cond(
                    MenuAuthState.has_modules,
                    "Cette destination n’est pas disponible avec vos droits actuels. Choisissez un accès autorisé ci-dessous.",
                    "Votre compte est connecté, mais aucun module n’est activé pour vous. Contactez le responsable des accès de votre exploitation.",
                ),
                role="status",
                class_name="mt-4 max-w-lg text-[13px] leading-relaxed text-[#C9C5B4]/70",
            ),
            rx.el.nav(
                rx.foreach(
                    NavigationState.visible_navigation,
                    lambda entry: rx.el.a(
                        rx.icon(
                            entry["icon"], class_name="h-4 w-4 shrink-0 text-[#D8FA5E]"
                        ),
                        rx.el.span(entry["label"], class_name="flex-1 text-[12px]"),
                        rx.icon("arrow-up-right", class_name="h-3.5 w-3.5 opacity-40"),
                        href=entry["href"],
                        class_name=(
                            "ap-mono flex items-center gap-3 border border-[#F2EFE4]/12 "
                            "px-4 py-3 uppercase tracking-[0.12em] text-[#F2EFE4] "
                            "transition-colors hover:border-[#D8FA5E]/50 hover:text-[#D8FA5E]"
                        ),
                    ),
                ),
                aria_label="Destinations autorisées",
                class_name="mt-8 grid grid-cols-1 gap-2 sm:grid-cols-2",
            ),
            rx.el.div(
                rx.el.button(
                    "Vérifier mes accès",
                    type="button",
                    on_click=MenuAuthState.retry_page,
                    class_name=(
                        "ap-mono border border-[#D8FA5E] bg-[#D8FA5E] px-4 py-3 "
                        "text-[9px] uppercase tracking-[0.18em] text-[#0A0A08]"
                    ),
                ),
                account_controls(),
                class_name="mt-8 flex flex-wrap items-center gap-3",
            ),
            class_name=(
                "mx-auto w-full max-w-3xl border border-[#F2EFE4]/12 bg-[#101208] "
                "p-6 sm:p-10"
            ),
        ),
        class_name=(
            "flex min-h-dvh w-full items-center justify-center bg-[#0A0A08] px-4 "
            "py-12 font-['Inter_Tight'] text-[#F2EFE4]"
        ),
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
