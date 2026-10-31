import reflex as rx

from app.components.menu_configuration import menu_configuration_panel
from app.states.menu_configuration_state import MenuConfigurationState as State


def search_field(
    label: str, identifier: str, value, handler: rx.event.EventType
) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=identifier,
            class_name="mb-2 block text-sm text-[#c9c5b4]",
        ),
        rx.el.input(
            id=identifier,
            default_value=value,
            on_change=handler.debounce(500),
            class_name="w-full rounded-none border border-[#f2efe4]/22 bg-[#0A0A08] px-4 py-3 text-sm text-[#f2efe4] focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
        ),
        class_name="w-full",
    )


def filter_buttons(
    options: list[str], value, handler: rx.event.EventType
) -> rx.Component:
    return rx.el.div(
        rx.foreach(
            options,
            lambda label: rx.el.button(
                label,
                on_click=handler(label),
                aria_pressed=value == label,
                class_name=rx.cond(
                    value == label,
                    "rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/10 px-3 py-2 text-xs text-[#e4ff9b] focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
                    "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-2 text-xs text-[#c9c5b4] focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
                ),
            ),
        ),
        class_name="my-3 flex flex-wrap gap-2",
        role="group",
        aria_label="Filtres",
    )


def override_controls(target, explicit) -> rx.Component:
    return rx.el.div(
        rx.foreach(
            [
                {"label": "Hériter", "mode": "inherit", "code": "n"},
                {"label": "Accorder", "mode": "grant", "code": "1"},
                {"label": "Refuser", "mode": "deny", "code": "0"},
            ],
            lambda option: rx.el.button(
                option["label"],
                aria_label=f"{option['label']} : {target}",
                aria_pressed=explicit == option["code"],
                on_click=State.edit(target, option["mode"]),
                disabled=State.saving,
                class_name=rx.cond(
                    explicit == option["code"],
                    "rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/10 px-3 py-2 text-xs text-[#e4ff9b] disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-[#ff8a5b]",
                    "rounded-none border border-[#f2efe4]/16 bg-[#0A0A08] px-3 py-2 text-xs text-[#c9c5b4] disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-[#ff8a5b]",
                ),
            ),
        ),
        class_name="flex flex-wrap gap-1",
        role="group",
        aria_label=f"Surcharge de {target}",
    )


def permission_row(row) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                row["key"],
                class_name="break-all text-sm font-semibold text-[#f2efe4]",
            ),
            rx.el.p(
                rx.cond(
                    row["inherited"], "Hérité : accordé", "Hérité : non accordé"
                ),
                class_name="mt-1 text-xs text-[#c9c5b4]/80",
            ),
            rx.el.p(
                row["source"], class_name="mt-1 text-xs text-[#c9c5b4]/75"
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.span(
            rx.cond(
                row["effective"], "Effectif : accordé", "Effectif : refusé"
            ),
            class_name=rx.cond(
                row["effective"],
                "w-fit text-xs text-[#d8fa5e]",
                "w-fit text-xs text-[#ffb894]",
            ),
        ),
        override_controls(row["target"], row["explicit"]),
        key=row["key"],
        class_name="flex flex-wrap items-center gap-4 border-b border-[#f2efe4]/12 p-4",
    )


def permission_editor() -> rx.Component:
    return rx.el.section(
        rx.el.h2(
            "Permissions effectives",
            class_name="ap-serif text-3xl text-[#f2efe4]",
        ),
        rx.el.p(
            "Recalculées depuis la politique actuelle à chaque chargement. Hériter supprime la surcharge ; un refus reste prioritaire sur les accords cumulés.",
            class_name="my-3 text-sm text-[#ffb894]",
        ),
        search_field(
            "Rechercher une permission (module ou action)",
            "permission-search",
            State.permission_search,
            State.set_permission_search,
        ),
        filter_buttons(
            ["Tous", "Accordés", "Refusés", "Explicites"],
            State.permission_filter,
            State.set_permission_filter,
        ),
        rx.el.p(
            f"{State.filtered_permissions.length()} permission(s)",
            aria_live="polite",
            class_name="mb-3 text-xs text-[#c9c5b4]/75",
        ),
        rx.cond(
            State.filtered_permissions.length() > 0,
            rx.el.div(
                rx.foreach(State.filtered_permissions, permission_row),
                class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160F]",
            ),
            empty_card("Aucune permission ne correspond aux filtres."),
        ),
        class_name="mt-6 w-full",
    )


def empty_card(message: str) -> rx.Component:
    return rx.el.div(
        rx.icon("inbox", class_name="mx-auto h-7 w-7 text-[#ff8a5b]"),
        rx.el.p(message, class_name="mt-3 text-sm text-[#c9c5b4]"),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160F] p-8 text-center",
    )


def role_card(row) -> rx.Component:
    return rx.el.button(
        rx.el.h3(
            row["label"], class_name="text-base font-semibold text-[#f2efe4]"
        ),
        rx.el.p(row["note"], class_name="my-2 text-xs text-[#c9c5b4]/80"),
        rx.el.p(
            f"{row['key']} · {row['overrides']} surcharge(s)",
            class_name="text-xs text-[#d8fa5e]",
        ),
        on_click=State.select_role(row["key"]),
        aria_pressed=State.selected_role == row["key"],
        key=row["key"],
        class_name=rx.cond(
            State.selected_role == row["key"],
            "w-full rounded-none border border-[#d8fa5e]/60 bg-[#d8fa5e]/5 p-5 text-left focus-visible:outline-2 focus-visible:outline-[#ff8a5b]",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#14160F] p-5 text-left hover:border-[#d8fa5e]/40 focus-visible:outline-2 focus-visible:outline-[#ff8a5b]",
        ),
    )


def roles_panel() -> rx.Component:
    return rx.el.section(
        search_field(
            "Rechercher un rôle enregistré",
            "role-search",
            State.role_search,
            State.set_role_search,
        ),
        filter_buttons(
            ["Tous", "Personnalisés"], State.role_filter, State.set_role_filter
        ),
        rx.cond(
            State.filtered_roles.length() > 0,
            rx.el.div(
                rx.foreach(State.filtered_roles, role_card),
                class_name="grid w-full grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3",
            ),
            empty_card("Aucun rôle ne correspond à la recherche."),
        ),
        rx.cond(
            State.selected_role != "",
            permission_editor(),
            empty_card(
                "Sélectionnez un rôle pour consulter et modifier ses permissions."
            ),
        ),
        class_name="w-full space-y-4",
    )


def account_card(row) -> rx.Component:
    return rx.el.button(
        rx.el.h3(
            row["email"],
            class_name="break-all text-sm font-semibold text-[#f2efe4]",
        ),
        rx.el.p(
            f"Compte #{row['id']} · {row['local_match']}",
            class_name="mt-2 text-xs text-[#c9c5b4]/80",
        ),
        rx.el.p(
            rx.cond(row["active"], "Actif", "Désactivé"),
            " · ",
            rx.cond(
                row["admin"], "Configuration autorisée", "Sans administration"
            ),
            class_name="my-2 text-xs text-[#ffb894]",
        ),
        rx.el.p(
            rx.cond(
                row["roles"].length() > 0,
                row["roles"].join(" · "),
                "Aucun rôle attribué",
            ),
            class_name="break-all text-xs text-[#d8fa5e]",
        ),
        on_click=State.select_account(row["id"]),
        aria_pressed=State.selected_account == row["id"],
        key=row["id"],
        class_name=rx.cond(
            State.selected_account == row["id"],
            "w-full rounded-none border border-[#d8fa5e]/60 bg-[#d8fa5e]/5 p-5 text-left focus-visible:outline-2 focus-visible:outline-[#ff8a5b]",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#14160F] p-5 text-left hover:border-[#d8fa5e]/40 focus-visible:outline-2 focus-visible:outline-[#ff8a5b]",
        ),
    )


def assignment_row(row) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                row["label"], class_name="text-sm font-semibold text-[#f2efe4]"
            ),
            rx.el.p(
                rx.cond(row["assigned"], "Attribué", "Non attribué"),
                class_name="mt-1 text-xs text-[#ffb894]",
            ),
        ),
        override_controls(row["target"], row["explicit"]),
        key=row["key"],
        class_name="flex flex-wrap items-center justify-between gap-3 rounded-none border border-[#f2efe4]/12 bg-[#14160F] p-4",
    )


def account_detail() -> rx.Component:
    return rx.el.section(
        rx.el.h2(
            State.selected_email,
            class_name="break-all ap-serif text-3xl text-[#f2efe4]",
        ),
        rx.el.div(
            rx.el.p(
                rx.cond(
                    State.selected_active,
                    "Compte actif",
                    "Compte désactivé (politique ou utilisateur local)",
                ),
                class_name="text-sm text-[#ffb894]",
            ),
            rx.el.p(
                "Accorder active le compte, Refuser le désactive. Un statut local inactif reste prioritaire.",
                class_name="text-xs text-[#c9c5b4]/80",
            ),
            override_controls(State.active_target, State.active_explicit),
            class_name="my-4 flex flex-wrap items-center gap-4",
        ),
        rx.el.h3(
            "Rôles multiples",
            class_name="mb-3 text-lg font-semibold text-[#f2efe4]",
        ),
        rx.el.p(
            "Accorder attribue le rôle ; Refuser le retire, y compris s’il est hérité. Hériter rétablit les rôles locaux et l’amorçage existant.",
            class_name="mb-4 text-sm text-[#c9c5b4]/80",
        ),
        rx.el.div(
            rx.foreach(State.assignments, assignment_row),
            class_name="grid w-full grid-cols-1 gap-3 lg:grid-cols-2",
        ),
        permission_editor(),
        class_name="mt-6 w-full rounded-none border border-[#f2efe4]/12 bg-[#14160F] p-4 sm:p-6",
    )


def accounts_panel() -> rx.Component:
    return rx.el.section(
        search_field(
            "Rechercher un compte connecté par e-mail",
            "account-search",
            State.account_search,
            State.set_account_search,
        ),
        filter_buttons(
            ["Tous", "Actifs", "Désactivés", "Administrateurs"],
            State.account_filter,
            State.set_account_filter,
        ),
        rx.el.p(
            "Uniquement les comptes réellement enregistrés par la connexion existante. Aucun compte n’est créé ici. Les filtres utilisent les droits et statuts actuels.",
            class_name="mb-4 text-sm text-[#c9c5b4]/80",
        ),
        rx.cond(
            State.accounts.length() > 0,
            rx.el.div(
                rx.foreach(State.accounts, account_card),
                class_name="grid w-full grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3",
            ),
            empty_card(
                "Aucun compte connecté disponible sur cette page ou pour ces filtres."
            ),
        ),
        rx.el.div(
            rx.el.button(
                "Précédent",
                on_click=State.account_page(-1),
                disabled=State.account_offset == 0,
                class_name="rounded-none border border-[#f2efe4]/22 bg-[#14160f] px-4 py-2 text-sm text-[#d8fa5e] disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
            ),
            rx.el.p(
                f"{State.account_total} compte(s) correspondant aux filtres · début {State.account_offset}",
                class_name="text-xs text-[#c9c5b4]/80",
            ),
            rx.el.button(
                "Suivant",
                on_click=State.account_page(1),
                disabled=State.account_offset + 25 >= State.account_total,
                class_name="rounded-none border border-[#f2efe4]/22 bg-[#14160f] px-4 py-2 text-sm text-[#d8fa5e] disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
            ),
            class_name="my-4 flex flex-wrap items-center justify-between gap-3",
        ),
        rx.cond(
            State.selected_account != "",
            account_detail(),
            empty_card(
                "Sélectionnez un compte pour ses rôles et droits effectifs."
            ),
        ),
        class_name="w-full",
    )


def audit_card(row) -> rx.Component:
    return rx.el.article(
        rx.el.h3(
            row["target"],
            class_name="break-all text-sm font-semibold text-[#f2efe4]",
        ),
        rx.el.p(
            f"{row['before']} → {row['after']}",
            class_name="my-2 text-sm text-[#d8fa5e]",
        ),
        rx.el.p(
            row["actor"], class_name="break-all text-xs text-[#c9c5b4]/80"
        ),
        rx.el.p(row["date"], class_name="mt-1 text-xs text-[#ffb894]"),
        key=row["id"],
        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160F] p-5",
    )


def journal_panel() -> rx.Component:
    return rx.el.section(
        rx.el.h2(
            "Journal des modifications",
            class_name="ap-serif text-3xl text-[#f2efe4]",
        ),
        rx.el.p(
            "Historique ajouté uniquement lors d’un changement confirmé : auteur, date, valeur avant et après. Aucune édition ni suppression du journal depuis la Configuration.",
            class_name="my-4 text-sm text-[#c9c5b4]/80",
        ),
        rx.cond(
            State.audit.length() > 0,
            rx.el.div(
                rx.foreach(State.audit, audit_card),
                class_name="grid w-full grid-cols-1 gap-3 md:grid-cols-2",
            ),
            empty_card("Aucune modification journalisée."),
        ),
        rx.el.div(
            rx.el.button(
                "Précédent",
                on_click=State.journal_page(-1),
                disabled=State.audit_offset == 0,
                class_name="rounded-none border border-[#f2efe4]/22 bg-[#14160f] px-4 py-2 text-sm text-[#d8fa5e] disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
            ),
            rx.el.p(
                f"{State.audit_total} entrée(s) · début {State.audit_offset}",
                class_name="text-xs text-[#c9c5b4]/80",
            ),
            rx.el.button(
                "Suivant",
                on_click=State.journal_page(1),
                disabled=State.audit_offset + 50 >= State.audit_total,
                class_name="rounded-none border border-[#f2efe4]/22 bg-[#14160f] px-4 py-2 text-sm text-[#d8fa5e] disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
            ),
            class_name="mt-4 flex flex-wrap items-center justify-between gap-3",
        ),
        class_name="w-full",
    )


def configuration_administration() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.foreach(
                    ["Menus", "Rôles", "Utilisateurs", "Journal"],
                    lambda label: rx.el.button(
                        label,
                        on_click=State.set_tab(label),
                        aria_pressed=State.tab == label,
                        class_name=rx.cond(
                            State.tab == label,
                            "rounded-none bg-[#D8FA5E] px-4 py-3 text-sm font-semibold text-[#0A0A08] focus-visible:outline-2 focus-visible:outline-[#ff8a5b]",
                            "rounded-none bg-[#0A0A08] px-4 py-3 text-sm font-medium text-[#c9c5b4] hover:bg-[#14160f] focus-visible:outline-2 focus-visible:outline-[#ff8a5b]",
                        ),
                    ),
                ),
                role="group",
                aria_label="Sections de la Configuration",
                class_name="flex flex-wrap gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160F] p-2",
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-4 w-4"),
                "Actualiser les droits",
                on_click=State.load_configuration,
                disabled=State.saving,
                class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/22 bg-[#14160f] px-4 py-3 text-sm text-[#d8fa5e] disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-[#d8fa5e]",
            ),
            class_name="mb-6 flex flex-wrap items-center justify-between gap-3",
        ),
        rx.el.p(
            State.notice, role="status", class_name="mb-3 text-sm text-[#e4ff9b]"
        ),
        rx.cond(
            State.saving,
            rx.el.p(
                "Enregistrement sécurisé en cours…",
                role="status",
                class_name="mb-3 text-sm text-[#ffb894]",
            ),
            rx.fragment(),
        ),
        rx.match(
            State.tab,
            ("Menus", menu_configuration_panel()),
            ("Rôles", roles_panel()),
            ("Utilisateurs", accounts_panel()),
            ("Journal", journal_panel()),
            rx.fragment(),
        ),
        class_name="w-full",
    )
