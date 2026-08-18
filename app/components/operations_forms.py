import reflex as rx

from app.components.guide_help import guide_error, help_icon_button
from app.states.operations_state import Option, OperationsState

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


def _text(
    name: str, value: rx.Var, placeholder: str, kind: str = "text"
) -> rx.Component:
    return rx.el.input(
        type=kind,
        name=name,
        placeholder=placeholder,
        default_value=value,
        key=f"{name}-{OperationsState.form_key}",
        class_name=_INPUT,
    )


def _select(
    name: str,
    value: rx.Var,
    options: rx.Var[list[Option]],
    first_option: rx.Component = rx.fragment(),
) -> rx.Component:
    return rx.el.div(
        rx.el.select(
            first_option,
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            default_value=value,
            key=f"{name}-{OperationsState.form_key}",
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
    error: rx.Var,
    submit_label: str,
    on_submit: rx.event.EventType,
    on_close: rx.event.EventType,
    topic: str = "phyto",
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
                    help_icon_button("traitements"),
                    class_name="flex items-start gap-3 w-full",
                ),
                body,
                guide_error(error, "traitements", topic),
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
                    class_name="flex items-center justify-end gap-3 mt-6 border-t border-white/10 pt-5",
                ),
                on_submit=on_submit,
                reset_on_submit=True,
                class_name="w-full",
            ),
            class_name="w-full max-w-3xl max-h-[88vh] overflow-y-auto rounded-3xl border border-white/10 bg-[#061a11]/95 p-7 backdrop-blur-2xl",
        ),
        class_name="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm",
    )


def _intervention_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _field(
                "Intitulé du chantier",
                _text(
                    "title",
                    OperationsState.intervention_form["title"],
                    "Protection mildiou - relais fongicide",
                ),
                "Au moins 3 caractères.",
            ),
            _field(
                "Parcelle",
                _select(
                    "parcel_id",
                    OperationsState.intervention_form["parcel_id"],
                    OperationsState.parcel_options,
                ),
            ),
            _field(
                "Culture liée",
                _select(
                    "crop_id",
                    OperationsState.intervention_form["crop_id"],
                    OperationsState.crop_options,
                    rx.el.option("Sans culture liée", value=""),
                ),
            ),
            _field(
                "Type d'intervention",
                _select(
                    "type",
                    OperationsState.intervention_form["type"],
                    OperationsState.type_options,
                ),
            ),
            _field(
                "Statut",
                _select(
                    "status",
                    OperationsState.intervention_form["status"],
                    OperationsState.status_options,
                ),
            ),
            _field(
                "Date planifiée",
                _text(
                    "scheduled_date",
                    OperationsState.intervention_form["scheduled_date"],
                    "",
                    "date",
                ),
                "Obligatoire.",
            ),
            _field(
                "Date de réalisation",
                _text(
                    "done_date",
                    OperationsState.intervention_form["done_date"],
                    "",
                    "date",
                ),
                "Renseignée automatiquement si réalisée.",
            ),
            _field(
                "Opérateur",
                _text(
                    "operator",
                    OperationsState.intervention_form["operator"],
                    "Camille Roux",
                ),
            ),
            _field(
                "Matériel",
                _text(
                    "equipment",
                    OperationsState.intervention_form["equipment"],
                    "Pulvérisateur porté 1200 L",
                ),
            ),
            _field(
                "Surface traitée (ha)",
                _text(
                    "area_treated_ha",
                    OperationsState.intervention_form["area_treated_ha"],
                    "9.6",
                    "number",
                ),
            ),
            _field(
                "Volume de bouillie (L/ha)",
                _text(
                    "water_volume_l_ha",
                    OperationsState.intervention_form["water_volume_l_ha"],
                    "180",
                    "number",
                ),
            ),
            _field(
                "Durée (h)",
                _text(
                    "duration_hours",
                    OperationsState.intervention_form["duration_hours"],
                    "2.5",
                    "number",
                ),
            ),
            _field(
                "Coût (€)",
                _text(
                    "cost",
                    OperationsState.intervention_form["cost"],
                    "480",
                    "number",
                ),
            ),
            _field(
                "Cible / objectif",
                _text(
                    "target",
                    OperationsState.intervention_form["target"],
                    "Phytophthora infestans",
                ),
            ),
            _field(
                "Conditions météo",
                _text(
                    "weather_conditions",
                    OperationsState.intervention_form["weather_conditions"],
                    "Couvert, vent faible",
                ),
            ),
            _field(
                "Température (°C)",
                _text(
                    "temperature_c",
                    OperationsState.intervention_form["temperature_c"],
                    "18",
                    "number",
                ),
            ),
            _field(
                "Vent (km/h)",
                _text(
                    "wind_speed_kmh",
                    OperationsState.intervention_form["wind_speed_kmh"],
                    "9",
                    "number",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-6",
        ),
        rx.el.div(
            rx.el.span(
                "Intrant appliqué (facultatif)",
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
            ),
            rx.el.div(
                _field(
                    "Produit",
                    _select(
                        "product_id",
                        OperationsState.intervention_form["product_id"],
                        OperationsState.product_options,
                        rx.el.option("Aucun intrant", value=""),
                    ),
                ),
                _field(
                    "Dose par hectare",
                    _text(
                        "dose_per_ha",
                        OperationsState.intervention_form["dose_per_ha"],
                        "1.5",
                        "number",
                    ),
                    "La quantité totale est calculée sur la surface traitée.",
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3",
            ),
            rx.el.p(
                "Si le statut est « Réalisée », la sortie de stock correspondante est enregistrée automatiquement.",
                class_name="text-[10px] font-medium text-lime-200/70 mt-3",
            ),
            class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-5",
        ),
        _field(
            "Notes de chantier",
            rx.el.textarea(
                name="notes",
                placeholder="Conditions d'application, réglages, observations…",
                default_value=OperationsState.intervention_form["notes"],
                key=f"int-notes-{OperationsState.form_key}",
                rows="3",
                class_name=f"{_INPUT} resize-y",
            ),
        ),
        class_name="w-full",
    )


def _harvest_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _field(
                "Culture récoltée",
                _select(
                    "crop_id",
                    OperationsState.harvest_form["crop_id"],
                    OperationsState.crop_options,
                ),
            ),
            _field(
                "Date de récolte",
                _text(
                    "harvest_date",
                    OperationsState.harvest_form["harvest_date"],
                    "",
                    "date",
                ),
            ),
            _field(
                "Quantité récoltée",
                _text(
                    "quantity",
                    OperationsState.harvest_form["quantity"],
                    "158.4",
                    "number",
                ),
                "Strictement positive.",
            ),
            _field(
                "Unité",
                _text("unit", OperationsState.harvest_form["unit"], "t"),
            ),
            _field(
                "Surface récoltée (ha)",
                _text(
                    "area_harvested_ha",
                    OperationsState.harvest_form["area_harvested_ha"],
                    "22",
                    "number",
                ),
                "Sert au calcul du rendement.",
            ),
            _field(
                "Humidité (%)",
                _text(
                    "moisture_percent",
                    OperationsState.harvest_form["moisture_percent"],
                    "14",
                    "number",
                ),
                "Entre 0 et 45 %.",
            ),
            _field(
                "Qualité",
                _select(
                    "quality",
                    OperationsState.harvest_form["quality"],
                    OperationsState.quality_options,
                ),
            ),
            _field(
                "Pertes (%)",
                _text(
                    "loss_percent",
                    OperationsState.harvest_form["loss_percent"],
                    "2",
                    "number",
                ),
            ),
            _field(
                "Prix unitaire (€)",
                _text(
                    "unit_price",
                    OperationsState.harvest_form["unit_price"],
                    "215",
                    "number",
                ),
                "Le produit brut est calculé automatiquement.",
            ),
            _field(
                "Lieu de stockage",
                _text(
                    "storage_location",
                    OperationsState.harvest_form["storage_location"],
                    "Cellule 1",
                ),
            ),
            _field(
                "Opérateur",
                _text(
                    "operator",
                    OperationsState.harvest_form["operator"],
                    "ETA Vallée",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-6",
        ),
        rx.el.div(
            rx.el.label(
                rx.el.input(
                    type="checkbox",
                    name="close_crop",
                    default_value="1",
                    key=f"close-crop-{OperationsState.form_key}",
                    class_name="h-4 w-4 accent-lime-300 cursor-pointer",
                ),
                rx.el.span(
                    "Clore la fiche culturale (statut récoltée, cycle à 100 %)",
                    class_name="text-sm font-medium text-emerald-100/75",
                ),
                class_name="flex items-center gap-2.5 cursor-pointer w-fit",
            ),
            class_name="mt-5",
        ),
        _field(
            "Observations",
            rx.el.textarea(
                name="notes",
                placeholder="Calibrage, conditions de chantier, débouché…",
                default_value=OperationsState.harvest_form["notes"],
                key=f"harvest-notes-{OperationsState.form_key}",
                rows="3",
                class_name=f"{_INPUT} resize-y",
            ),
        ),
        class_name="w-full",
    )


def _movement_body() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _field(
                "Produit",
                _select(
                    "product_id",
                    OperationsState.movement_form["product_id"],
                    OperationsState.product_options,
                ),
            ),
            _field(
                "Nature du mouvement",
                _select(
                    "type",
                    OperationsState.movement_form["type"],
                    OperationsState.movement_options,
                ),
                "Un inventaire fixe le stock à la valeur saisie.",
            ),
            _field(
                "Quantité",
                _text(
                    "quantity",
                    OperationsState.movement_form["quantity"],
                    "500",
                    "number",
                ),
            ),
            _field(
                "Prix unitaire (€)",
                _text(
                    "unit_price",
                    OperationsState.movement_form["unit_price"],
                    "0.42",
                    "number",
                ),
            ),
            _field(
                "Date",
                _text(
                    "movement_date",
                    OperationsState.movement_form["movement_date"],
                    "",
                    "date",
                ),
            ),
            _field(
                "Référence",
                _text(
                    "reference",
                    OperationsState.movement_form["reference"],
                    "BL-2291",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-6",
        ),
        _field(
            "Commentaire",
            rx.el.textarea(
                name="notes",
                placeholder="Livraison, transfert entre sites, casse…",
                default_value=OperationsState.movement_form["notes"],
                key=f"mvt-notes-{OperationsState.form_key}",
                rows="3",
                class_name=f"{_INPUT} resize-y",
            ),
        ),
        class_name="w-full",
    )


def operations_modals() -> rx.Component:
    return rx.fragment(
        rx.cond(
            OperationsState.show_intervention_form,
            _modal_shell(
                OperationsState.intervention_form_title,
                "Fiche d'intervention",
                "spray-can",
                _intervention_body(),
                OperationsState.form_error,
                "Enregistrer l'intervention",
                OperationsState.submit_intervention,
                OperationsState.close_intervention_form,
                topic="phyto",
            ),
            rx.fragment(),
        ),
        rx.cond(
            OperationsState.show_harvest_form,
            _modal_shell(
                "Saisir une récolte",
                "Registre de récolte",
                "wheat",
                _harvest_body(),
                OperationsState.harvest_error,
                "Enregistrer la récolte",
                OperationsState.submit_harvest,
                OperationsState.close_harvest_form,
                topic="recolte",
            ),
            rx.fragment(),
        ),
        rx.cond(
            OperationsState.show_movement_form,
            _modal_shell(
                "Mouvement de stock",
                "Magasin d'intrants",
                "arrow-left-right",
                _movement_body(),
                OperationsState.movement_error,
                "Valider le mouvement",
                OperationsState.submit_movement,
                OperationsState.close_movement_form,
                topic="stock",
            ),
            rx.fragment(),
        ),
    )
