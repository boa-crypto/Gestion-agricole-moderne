import reflex as rx

from app.states.irrigation_state import IrrigationState


def irrigation_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.p(
                "AGRICULTURE · PILOTAGE HYDRIQUE",
                class_name="text-xs tracking-[0.24em] font-semibold text-lime-300",
            ),
            rx.el.h1(
                "Irrigation",
                class_name="font-['Instrument_Serif'] text-5xl sm:text-6xl text-emerald-50 mt-3",
            ),
            rx.el.p(
                "Anticiper les besoins, parcelle par parcelle. Un bilan indicatif sur les sept prochains jours, construit à partir des cultures, des stades observés et de la météo réelle.",
                class_name="mt-4 max-w-3xl text-sm leading-relaxed text-emerald-100/80",
            ),
        ),
        rx.el.button(
            rx.cond(
                IrrigationState.is_loading,
                rx.icon("loader-circle", class_name="h-4 w-4 animate-spin"),
                rx.icon("refresh-cw", class_name="h-4 w-4"),
            ),
            rx.cond(
                IrrigationState.is_loading,
                "Actualisation…",
                "Actualiser les recommandations",
            ),
            on_click=IrrigationState.load_irrigation,
            disabled=IrrigationState.is_loading,
            class_name="flex items-center justify-center gap-2 w-full sm:w-fit shrink-0 rounded-full bg-[#a3e635] px-5 py-3 text-sm font-semibold text-[#04120c] hover:bg-lime-200 disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-lime-300",
        ),
        class_name="flex flex-col xl:flex-row xl:items-end justify-between gap-6 border-b border-white/10 pb-8 mt-8",
    )


def metric(label: str, value, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.p(label, class_name="text-xs text-emerald-100/75"),
        rx.el.p(
            value,
            rx.el.span(unit, class_name="ml-1 text-xs text-emerald-100/75"),
            class_name="mt-2 text-2xl font-semibold text-emerald-50 tabular-nums",
        ),
        class_name="rounded-2xl bg-white/[0.03] border border-white/10 p-4 min-w-0",
    )


def forecast_day(day) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            day["date"], class_name="text-xs font-semibold text-emerald-50"
        ),
        rx.el.p(
            f"Pluie {day['rain']:.1f} mm",
            class_name="mt-2 text-xs text-emerald-100/80",
        ),
        rx.el.p(
            f"ET0 {day['et0']:.1f} mm", class_name="mt-1 text-xs text-lime-200"
        ),
        class_name="rounded-xl border border-white/10 bg-white/[0.03] p-3",
    )


def recommendation_details(card) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Prochain tour indicatif",
                    class_name="text-xs font-semibold uppercase tracking-wider text-lime-300",
                ),
                rx.el.p(
                    f"{card['recommendation']['dose']} mm",
                    class_name="font-['Instrument_Serif'] text-5xl text-emerald-50 mt-2",
                ),
                rx.el.p(
                    f"{card['recommendation']['volume']} m³ · 1 mm / ha = 10 m³",
                    class_name="mt-2 text-sm text-lime-200",
                ),
            ),
            rx.el.div(
                rx.el.p(
                    card["recommendation"]["message"],
                    class_name="text-sm font-semibold text-emerald-50",
                ),
                rx.cond(
                    card["recommendation"]["date"] != "",
                    rx.el.p(
                        f"À envisager le {card['recommendation']['date']}",
                        class_name="mt-2 text-sm text-amber-200",
                    ),
                    rx.el.p(
                        "Aucune date de tour proposée",
                        class_name="mt-2 text-sm text-emerald-100/80",
                    ),
                ),
                rx.el.p(
                    f"Horizon : {card['recommendation']['period']}",
                    class_name="mt-2 text-xs text-emerald-100/80",
                ),
            ),
            class_name="flex flex-col sm:flex-row sm:items-center justify-between gap-5 rounded-2xl border border-lime-300/25 bg-lime-300/5 p-5",
        ),
        rx.el.div(
            metric(
                "Besoin ETc sur 7 jours", card["recommendation"]["etc"], "mm"
            ),
            metric(
                "Pluie efficace (80 %)",
                card["recommendation"]["effective_rain"],
                "mm",
            ),
            metric(
                "Apports récents déduits",
                card["recommendation"]["recent"],
                "mm",
            ),
            metric(
                "Déficit indicatif", card["recommendation"]["deficit"], "mm"
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Culture & phénologie",
                    class_name="text-base font-semibold text-emerald-50",
                ),
                rx.el.p(
                    card["recommendation"]["water_need"],
                    class_name="mt-3 text-sm text-lime-200",
                ),
                rx.el.p(
                    card["recommendation"]["requirement"],
                    class_name="mt-2 text-xs text-emerald-100/80",
                ),
                rx.el.p(
                    card["recommendation"]["phenology"],
                    class_name="mt-3 text-sm text-emerald-100/90",
                ),
                rx.el.p(
                    f"Kc ajusté : {card['recommendation']['kc']}",
                    class_name="mt-2 text-sm text-lime-200",
                ),
                rx.el.p(
                    card["recommendation"]["profile"],
                    class_name="mt-3 text-xs leading-relaxed text-emerald-100/80",
                ),
            ),
            rx.el.div(
                rx.el.h3(
                    "Pourquoi cette recommandation ?",
                    class_name="text-base font-semibold text-emerald-50",
                ),
                rx.el.p(
                    card["recommendation"]["rationale"],
                    class_name="mt-3 text-sm leading-relaxed text-emerald-100/90",
                ),
                rx.el.p(
                    "Les apports réalisés sont convertis depuis les L/ha (10 000 L/ha = 1 mm), pondérés par la surface traitée. Les apports non rattachés à cette culture ne sont pas déduits.",
                    class_name="mt-3 text-xs leading-relaxed text-emerald-100/80",
                ),
                rx.el.p(
                    card["recommendation"]["assumptions"],
                    class_name="mt-3 text-xs leading-relaxed text-amber-200",
                ),
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-6",
        ),
        rx.el.details(
            rx.el.summary(
                "Voir les 7 jours de pluie et d’ET0",
                class_name="cursor-pointer text-sm font-semibold text-lime-200 focus-visible:outline-2 focus-visible:outline-lime-300",
            ),
            rx.el.div(
                rx.foreach(card["days"], forecast_day),
                class_name="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-7 gap-2 mt-4 w-full",
            ),
            rx.el.p(
                f"ET0 cumulée : {card['recommendation']['et0']} mm · pluie cumulée : {card['recommendation']['rain']} mm",
                class_name="mt-3 text-xs text-emerald-100/80",
            ),
            class_name="border-t border-white/10 pt-4",
        ),
        class_name="flex flex-col gap-5 mt-5",
    )


def irrigation_card(card) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    card["parcel"],
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50",
                ),
                rx.el.p(
                    card["crop"],
                    class_name="mt-2 text-sm font-semibold text-lime-200",
                ),
                rx.el.p(
                    card["area"], class_name="mt-2 text-xs text-emerald-100/80"
                ),
            ),
            rx.el.span(
                card["system"],
                class_name="w-fit rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs text-emerald-50",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.cond(
            card["recommendation"]["status"] != "ready",
            rx.el.div(
                rx.el.p(
                    card["recommendation"]["water_need"],
                    class_name="mt-3 text-sm text-lime-200",
                ),
                rx.el.p(
                    card["recommendation"]["phenology"],
                    class_name="mt-2 text-xs text-emerald-100/80",
                ),
            ),
            rx.fragment(),
        ),
        rx.el.p(
            card["position"], class_name="mt-4 text-xs text-emerald-100/75"
        ),
        rx.cond(
            card["source"] != "",
            rx.el.p(
                card["source"], class_name="mt-2 text-xs text-emerald-100/80"
            ),
            rx.fragment(),
        ),
        rx.cond(
            card["recommendation"]["status"] == "ready",
            recommendation_details(card),
            rx.el.div(
                rx.icon("info", class_name="h-5 w-5 shrink-0 text-amber-200"),
                rx.el.p(
                    card["recommendation"]["message"],
                    class_name="text-sm leading-relaxed text-amber-100",
                ),
                role="status",
                class_name="mt-5 flex items-start gap-3 rounded-2xl border border-amber-300/20 bg-amber-300/5 p-5",
            ),
        ),
        key=card["key"],
        class_name="w-full min-w-0 rounded-3xl border border-white/10 bg-white/[0.03] p-5 sm:p-7",
    )


def irrigation_workspace() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.label(
                "Choisir une parcelle",
                html_for="irrigation-parcel",
                class_name="block mb-2 text-sm font-semibold text-emerald-50",
            ),
            rx.el.div(
                rx.el.select(
                    rx.el.option("Toutes les parcelles", value="all"),
                    rx.foreach(
                        IrrigationState.parcel_options,
                        lambda item: rx.el.option(
                            item["name"], value=item["id"]
                        ),
                    ),
                    id="irrigation-parcel",
                    value=IrrigationState.selected_parcel,
                    on_change=IrrigationState.select_parcel,
                    class_name="appearance-none w-full rounded-xl border border-lime-300/25 bg-[#04120c] py-3 pl-4 pr-10 text-sm text-emerald-50 focus-visible:outline-2 focus-visible:outline-lime-300",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="pointer-events-none absolute right-3 top-3.5 h-4 w-4 text-lime-300",
                ),
                class_name="relative w-full sm:max-w-md",
            ),
        ),
        rx.el.p(
            "Aide à la décision, pas une mesure de l’humidité du sol. Ce bilan prévisionnel ne connaît ni la réserve utile, ni les restrictions locales, ni l’efficacité du matériel. Vérifiez le sol, le stade et les contraintes avant tout apport.",
            class_name="rounded-2xl border border-amber-300/20 bg-amber-300/5 p-4 text-sm leading-relaxed text-amber-100",
        ),
        rx.cond(
            IrrigationState.notice != "",
            rx.el.p(
                IrrigationState.notice, class_name="text-sm text-amber-200"
            ),
            rx.fragment(),
        ),
        rx.match(
            rx.cond(
                IrrigationState.is_loading,
                "loading",
                rx.cond(
                    IrrigationState.error != "",
                    "error",
                    rx.cond(
                        IrrigationState.cards.length() == 0, "empty", "ready"
                    ),
                ),
            ),
            (
                "loading",
                rx.el.div(
                    rx.icon(
                        "loader-circle",
                        class_name="h-5 w-5 text-lime-300 animate-spin",
                    ),
                    rx.el.p(
                        "Lecture des cultures et actualisation des prévisions Open-Meteo…",
                        class_name="text-sm text-emerald-50",
                    ),
                    role="status",
                    class_name="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-8",
                ),
            ),
            (
                "error",
                rx.el.p(
                    IrrigationState.error,
                    role="alert",
                    class_name="rounded-2xl border border-amber-300/25 bg-amber-300/5 p-8 text-amber-100",
                ),
            ),
            (
                "empty",
                rx.el.div(
                    rx.icon("droplets", class_name="h-8 w-8 text-lime-300"),
                    rx.el.h2(
                        "Aucune parcelle disponible",
                        class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-4",
                    ),
                    rx.el.p(
                        "Aucune donnée parcellaire à analyser. Aucune culture ni météo fictive n’a été ajoutée.",
                        class_name="mt-3 text-sm text-emerald-100/80",
                    ),
                    class_name="rounded-3xl border border-white/10 bg-white/[0.03] p-8",
                ),
            ),
            rx.el.div(
                rx.foreach(IrrigationState.visible_cards, irrigation_card),
                class_name="flex flex-col gap-5 w-full",
            ),
        ),
        aria_label="Recommandations d’irrigation",
        aria_busy=IrrigationState.is_loading,
        class_name="mt-8 flex flex-col gap-5 w-full min-w-0",
    )
