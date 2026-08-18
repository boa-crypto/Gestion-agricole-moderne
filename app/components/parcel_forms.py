import reflex as rx

from app.components.guide_help import guide_error, help_icon_button
from app.states.parcels_state import Option, ParcelsState

_INPUT = "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors"
_LABEL = "block text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45 mb-1.5"


def _field(label: str, control: rx.Component, hint: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name=_LABEL),
        control,
        rx.el.p(
            hint,
            class_name="text-[10px] font-medium text-emerald-100/35 mt-1",
        ),
        class_name="w-full min-w-0",
    )


def _text_input(
    name: str, value: rx.Var, placeholder: str, kind: str = "text"
) -> rx.Component:
    return rx.el.input(
        type=kind,
        name=name,
        placeholder=placeholder,
        default_value=value,
        key=f"{name}-{ParcelsState.form_key}",
        class_name=_INPUT,
    )


def _select_field(
    name: str,
    value: rx.Var,
    options: rx.Var[list[Option]],
) -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            default_value=value,
            key=f"{name}-{ParcelsState.form_key}",
            class_name=f"{_INPUT} appearance-none cursor-pointer pr-9",
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full",
    )


def _modal_shell(
    title: rx.Var | str,
    subtitle: str,
    icon: str,
    body: rx.Component,
    submit_label: str,
    on_submit: rx.event.EventType,
    on_close: rx.event.EventType,
    topic: str = "surface",
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.form(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.icon(icon, class_name="h-4 w-4 text-lime-300"),
                            rx.el.span(
                                subtitle,
                                class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                            ),
                            class_name="flex items-center gap-2",
                        ),
                        rx.el.h2(
                            title,
                            class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                        ),
                        class_name="min-w-0 flex-1",
                    ),
                    help_icon_button("parcelles"),
                    class_name="flex items-start gap-3 w-full",
                ),
                body,
                guide_error(ParcelsState.form_error, "parcelles", topic),
                rx.el.div(
                    rx.el.button(
                        "Annuler",
                        type="button",
                        on_click=on_close,
                        class_name="rounded-xl border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-semibold text-emerald-100/70 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
                    ),
                    rx.el.button(
                        rx.icon("check", class_name="h-4 w-4 text-[#04140d]"),
                        rx.el.span(submit_label, class_name="text-[#04140d]"),
                        type="submit",
                        class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-5 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                    ),
                    class_name="flex items-center justify-end gap-3 mt-6 border-t border-white/10 pt-5 flex-wrap w-full",
                ),
                on_submit=on_submit,
                reset_on_submit=True,
                class_name="w-full",
            ),
            class_name="w-full max-w-3xl max-h-[88vh] overflow-y-auto rounded-3xl border border-white/10 bg-[#061a11]/95 p-7 backdrop-blur-2xl",
        ),
        class_name="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm",
    )


def _parcel_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _field(
                "Nom de la parcelle",
                _text_input(
                    "name",
                    ParcelsState.parcel_form["name"],
                    "Les Grands Champs",
                ),
                "Au moins 2 caractères.",
            ),
            _field(
                "Code îlot",
                _text_input("code", ParcelsState.parcel_form["code"], "P08"),
                "Identifiant court unique.",
            ),
            _field(
                "Surface (ha)",
                _text_input(
                    "area_ha",
                    ParcelsState.parcel_form["area_ha"],
                    "12.5",
                    "number",
                ),
                "Strictement positive.",
            ),
            _field(
                "Statut",
                _select_field(
                    "status",
                    ParcelsState.parcel_form["status"],
                    ParcelsState.status_options,
                ),
            ),
            _field(
                "Type de sol",
                _select_field(
                    "soil_type",
                    ParcelsState.parcel_form["soil_type"],
                    ParcelsState.soil_options,
                ),
            ),
            _field(
                "Irrigation",
                _select_field(
                    "irrigation",
                    ParcelsState.parcel_form["irrigation"],
                    ParcelsState.irrigation_options,
                ),
            ),
            _field(
                "Localité",
                _text_input(
                    "locality",
                    ParcelsState.parcel_form["locality"],
                    "Plateau de Beauce",
                ),
            ),
            _field(
                "pH",
                _text_input(
                    "ph", ParcelsState.parcel_form["ph"], "7.0", "number"
                ),
                "Entre 3 et 10.",
            ),
            _field(
                "Matière organique (%)",
                _text_input(
                    "organic_matter_percent",
                    ParcelsState.parcel_form["organic_matter_percent"],
                    "2.5",
                    "number",
                ),
            ),
            _field(
                "Pente (%)",
                _text_input(
                    "slope_percent",
                    ParcelsState.parcel_form["slope_percent"],
                    "1.5",
                    "number",
                ),
            ),
            _field(
                "Latitude",
                _text_input(
                    "latitude",
                    ParcelsState.parcel_form["latitude"],
                    "48.2345",
                    "number",
                ),
            ),
            _field(
                "Longitude",
                _text_input(
                    "longitude",
                    ParcelsState.parcel_form["longitude"],
                    "1.8452",
                    "number",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-6",
        ),
        rx.el.div(
            rx.el.span(
                "Position sur la carte d'assolement (%)",
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
            ),
            rx.el.div(
                _field(
                    "X",
                    _text_input(
                        "map_x",
                        ParcelsState.parcel_form["map_x"],
                        "6",
                        "number",
                    ),
                ),
                _field(
                    "Y",
                    _text_input(
                        "map_y",
                        ParcelsState.parcel_form["map_y"],
                        "6",
                        "number",
                    ),
                ),
                _field(
                    "Largeur",
                    _text_input(
                        "map_w",
                        ParcelsState.parcel_form["map_w"],
                        "24",
                        "number",
                    ),
                ),
                _field(
                    "Hauteur",
                    _text_input(
                        "map_h",
                        ParcelsState.parcel_form["map_h"],
                        "26",
                        "number",
                    ),
                ),
                class_name="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3",
            ),
            class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-5",
        ),
        rx.el.div(
            rx.el.label(
                rx.el.input(
                    type="checkbox",
                    name="is_organic",
                    default_checked=ParcelsState.parcel_form["is_organic"]
                    == "1",
                    key=f"organic-{ParcelsState.form_key}",
                    class_name="h-4 w-4 accent-lime-300 cursor-pointer",
                    default_value="1",
                ),
                rx.el.span(
                    "Parcelle conduite en agriculture biologique",
                    class_name="text-sm font-medium text-emerald-100/75",
                ),
                class_name="flex items-center gap-2.5 cursor-pointer w-fit",
            ),
            class_name="mt-5",
        ),
        _field(
            "Notes agronomiques",
            rx.el.textarea(
                name="notes",
                placeholder="Drainage, historique, contraintes…",
                default_value=ParcelsState.parcel_form["notes"],
                key=f"parcel-notes-{ParcelsState.form_key}",
                rows="3",
                class_name=f"{_INPUT} resize-y",
            ),
        ),
        class_name="w-full",
    )


def _catalog_hint() -> rx.Component:
    """Rappel du référentiel structuré dans le formulaire de culture."""
    return rx.el.div(
        rx.el.div(
            rx.icon("sprout", class_name="h-4 w-4 text-lime-300"),
            class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/10",
        ),
        rx.el.div(
            rx.el.p(
                f"{ParcelsState.catalog_variety_count} variétés du référentiel disponibles",
                class_name="text-sm font-semibold text-emerald-50",
            ),
            rx.el.p(
                "Choisir la variété relie la fiche culturale à sa catégorie, "
                "sa culture et son espèce botanique : cycle, besoin en eau, "
                "qualité et rendement de référence en découlent.",
                class_name="text-[11px] font-medium text-emerald-100/50 mt-0.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.a(
            rx.icon("arrow-up-right", class_name="h-3.5 w-3.5 text-lime-200"),
            rx.el.span("Référentiel", class_name="text-lime-200"),
            href="/referentiel",
            class_name="flex items-center gap-1.5 rounded-full border border-lime-300/30 bg-lime-300/10 px-3 py-1.5 text-[11px] font-semibold hover:bg-lime-300/20 transition-colors w-fit shrink-0",
        ),
        class_name="flex flex-col sm:flex-row sm:items-center gap-3 w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-6",
    )


def _crop_body() -> rx.Component:
    return rx.el.div(
        _catalog_hint(),
        rx.el.div(
            _field(
                "Nom de la culture",
                _text_input(
                    "name",
                    ParcelsState.crop_form["name"],
                    "Blé tendre Rubisko",
                ),
                "Au moins 2 caractères.",
            ),
            _field(
                "Variété du référentiel",
                rx.el.div(
                    rx.el.select(
                        rx.el.option("Sans variété liée", value=""),
                        rx.foreach(
                            ParcelsState.variety_options,
                            lambda opt: rx.el.option(
                                opt["label"], value=opt["value"]
                            ),
                        ),
                        name="variety_id",
                        default_value=ParcelsState.crop_form["variety_id"],
                        key=f"variety-{ParcelsState.form_key}",
                        class_name=f"{_INPUT} appearance-none cursor-pointer pr-9",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                    ),
                    class_name="relative w-full",
                ),
                "Lecture Catégorie · Culture · Espèce — Variété.",
            ),
            _field(
                "Campagne",
                _text_input("season", ParcelsState.crop_form["season"], "2026"),
            ),
            _field(
                "Surface implantée (ha)",
                _text_input(
                    "area_ha",
                    ParcelsState.crop_form["area_ha"],
                    "12.5",
                    "number",
                ),
                "Ne peut dépasser la surface de la parcelle.",
            ),
            _field(
                "Stade phénologique",
                _select_field(
                    "stage",
                    ParcelsState.crop_form["stage"],
                    ParcelsState.stage_options,
                ),
            ),
            _field(
                "Statut",
                _select_field(
                    "status",
                    ParcelsState.crop_form["status"],
                    ParcelsState.crop_status_options,
                ),
            ),
            _field(
                "État sanitaire",
                _select_field(
                    "health",
                    ParcelsState.crop_form["health"],
                    ParcelsState.health_options,
                ),
            ),
            _field(
                "Avancement (%)",
                _text_input(
                    "progress_percent",
                    ParcelsState.crop_form["progress_percent"],
                    "0",
                    "number",
                ),
                "Entre 0 et 100.",
            ),
            _field(
                "Densité de semis",
                _text_input(
                    "seed_density",
                    ParcelsState.crop_form["seed_density"],
                    "320",
                    "number",
                ),
            ),
            _field(
                "Rendement visé (t/ha)",
                _text_input(
                    "expected_yield_t_ha",
                    ParcelsState.crop_form["expected_yield_t_ha"],
                    "8.4",
                    "number",
                ),
            ),
            _field(
                "Date de semis",
                _text_input(
                    "sowing_date",
                    ParcelsState.crop_form["sowing_date"],
                    "",
                    "date",
                ),
            ),
            _field(
                "Récolte prévue",
                _text_input(
                    "expected_harvest_date",
                    ParcelsState.crop_form["expected_harvest_date"],
                    "",
                    "date",
                ),
                "Doit suivre la date de semis.",
            ),
            _field(
                "Récolte réalisée",
                _text_input(
                    "actual_harvest_date",
                    ParcelsState.crop_form["actual_harvest_date"],
                    "",
                    "date",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-6",
        ),
        _field(
            "Observations",
            rx.el.textarea(
                name="notes",
                placeholder="Pression sanitaire, itinéraire technique…",
                default_value=ParcelsState.crop_form["notes"],
                key=f"crop-notes-{ParcelsState.form_key}",
                rows="3",
                class_name=f"{_INPUT} resize-y",
            ),
        ),
        class_name="w-full",
    )


def parcel_modals() -> rx.Component:
    return rx.fragment(
        rx.cond(
            ParcelsState.show_parcel_form,
            _modal_shell(
                ParcelsState.parcel_form_title,
                "Fiche parcellaire",
                "map",
                _parcel_body(),
                "Enregistrer la parcelle",
                ParcelsState.submit_parcel,
                ParcelsState.close_parcel_form,
                topic="surface",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ParcelsState.show_crop_form,
            _modal_shell(
                ParcelsState.crop_form_title,
                f"Parcelle {ParcelsState.parcel_detail['name']}",
                "sprout",
                _crop_body(),
                "Enregistrer la culture",
                ParcelsState.submit_crop,
                ParcelsState.close_crop_form,
                topic="dates",
            ),
            rx.fragment(),
        ),
    )
