"""Formulaire d'observation rapide du stade phénologique."""

import reflex as rx

from app.states.phenology_state import Option, PhenologyState

_INPUT = "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 outline-hidden transition-colors"
_LABEL = "block text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45 mb-1.5"


def _field(label: str, control: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name=_LABEL),
        control,
        class_name="w-full min-w-0",
    )


def _select(
    name: str,
    options: rx.Var[list[Option]],
    default: rx.Var | str,
    placeholder: str = "",
) -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.cond(
                placeholder != "",
                rx.el.option(placeholder, value=""),
                rx.fragment(),
            ),
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            default_value=default,
            key=f"{name}-{PhenologyState.form_key}",
            class_name=f"{_INPUT} appearance-none cursor-pointer pr-9",
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full",
    )


def _checkbox(name: str, label: str) -> rx.Component:
    return rx.el.label(
        rx.el.input(
            type="checkbox",
            name=name,
            default_value="1",
            key=f"{name}-{PhenologyState.form_key}",
            class_name="h-4 w-4 accent-lime-300 cursor-pointer",
        ),
        rx.el.span(label, class_name="text-sm font-medium text-emerald-100/75"),
        class_name="flex items-center gap-2.5 cursor-pointer w-fit",
    )


def _errors() -> rx.Component:
    return rx.cond(
        PhenologyState.form_error != "",
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "octagon-alert",
                    class_name="h-4 w-4 shrink-0 text-red-300",
                ),
                rx.el.span(
                    "Observation refusée : le stade doit appartenir au profil de la culture.",
                    class_name="text-[11px] font-semibold text-red-200",
                ),
                class_name="flex items-start gap-2",
            ),
            rx.foreach(
                PhenologyState.form_errors,
                lambda message: rx.el.p(
                    message,
                    class_name="text-[11px] font-medium text-red-100/75 mt-1.5 leading-relaxed",
                ),
            ),
            class_name="w-full rounded-xl border border-red-400/30 bg-red-500/10 p-3 mt-3",
        ),
        rx.fragment(),
    )


def phenology_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.div(
                rx.icon("clipboard-pen", class_name="h-4 w-4 text-lime-300"),
                rx.el.span(
                    "Observation rapide",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.p(
                "Le stade proposé est contrôlé face au profil de la culture : "
                "un stade étranger au cycle est refusé et rien n'est écrasé.",
                class_name="text-[11px] font-medium text-emerald-100/50 mt-1.5",
            ),
            class_name="min-w-0",
        ),
        rx.el.div(
            _field(
                "Date d'observation",
                rx.el.input(
                    type="date",
                    name="observed_on",
                    default_value=PhenologyState.today_iso,
                    key=f"obsdate-{PhenologyState.form_key}",
                    class_name=_INPUT,
                ),
            ),
            _field(
                "Heure (facultative)",
                rx.el.input(
                    type="time",
                    name="observed_at_time",
                    key=f"obstime-{PhenologyState.form_key}",
                    class_name=_INPUT,
                ),
            ),
            _field(
                "Stade observé",
                _select(
                    "stage",
                    PhenologyState.stage_choices,
                    "",
                    "Choisir un stade du profil",
                ),
            ),
            _field(
                "Statut",
                _select(
                    "status",
                    PhenologyState.status_options,
                    "CONFIRME",
                ),
            ),
            _field(
                "Observateur",
                rx.el.input(
                    name="observer",
                    placeholder="Technicien X",
                    key=f"obsobserver-{PhenologyState.form_key}",
                    class_name=_INPUT,
                ),
            ),
            _field(
                "Vigueur",
                rx.el.input(
                    name="vigour",
                    placeholder="Bonne, moyenne, faible…",
                    key=f"obsvigour-{PhenologyState.form_key}",
                    class_name=_INPUT,
                ),
            ),
            _field(
                "Homogénéité",
                rx.el.input(
                    name="homogeneity",
                    placeholder="Homogène, hétérogène en bordure…",
                    key=f"obshomog-{PhenologyState.form_key}",
                    class_name=_INPUT,
                ),
            ),
            _field(
                "Anomalies",
                rx.el.input(
                    name="anomalies",
                    placeholder="Zones jaunissantes, verse localisée…",
                    key=f"obsanom-{PhenologyState.form_key}",
                    class_name=_INPUT,
                ),
            ),
            _field(
                "Maladies observées",
                rx.el.input(
                    name="diseases_observed",
                    placeholder="Septoriose, mildiou…",
                    key=f"obsdis-{PhenologyState.form_key}",
                    class_name=_INPUT,
                ),
            ),
            _field(
                "Ravageurs observés",
                rx.el.input(
                    name="pests_observed",
                    placeholder="Pucerons, limaces…",
                    key=f"obspest-{PhenologyState.form_key}",
                    class_name=_INPUT,
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-5",
        ),
        rx.el.div(
            _checkbox("water_stress", "Stress hydrique constaté"),
            _checkbox("thermal_stress", "Stress thermique constaté"),
            class_name="flex flex-wrap items-center gap-6 mt-4",
        ),
        _field(
            "Commentaire agronomique",
            rx.el.textarea(
                name="comment",
                placeholder="Ce qui a été vu sur les placettes…",
                rows="3",
                key=f"obscomment-{PhenologyState.form_key}",
                class_name=f"{_INPUT} resize-y",
            ),
        ),
        _errors(),
        rx.el.button(
            rx.icon("check", class_name="h-4 w-4 text-[#04140d]"),
            rx.el.span("Consigner l'observation", class_name="text-[#04140d]"),
            type="submit",
            class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit mt-4",
        ),
        on_submit=PhenologyState.submit_observation,
        reset_on_submit=True,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-5 mt-4",
    )
