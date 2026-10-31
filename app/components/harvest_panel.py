import reflex as rx

from app.states.operations_state import HarvestRow, OperationsState, YieldRow


def _perf_badge(tone: rx.Var, value: rx.Var) -> rx.Component:
    return rx.el.span(
        f"{value}% de l'objectif",
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit whitespace-nowrap",
        ),
    )


def _harvest_row(harvest: HarvestRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.p(
                harvest["crop_name"],
                class_name="text-xs font-semibold text-[#f2efe4] truncate",
            ),
            rx.el.p(
                f"{harvest['species']} · {harvest['parcel']}",
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 truncate",
            ),
            class_name="px-3 py-2.5 align-middle min-w-[14rem]",
        ),
        rx.el.td(
            rx.el.span(
                harvest["date_label"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/60 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.span(
                f"{harvest['quantity']:.1f} {harvest['unit']}",
                class_name="text-xs font-semibold text-[#f2efe4] whitespace-nowrap",
            ),
            rx.el.p(
                f"{harvest['area_ha']:.1f} ha récoltés",
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    f"{harvest['yield_t_ha']:.1f}",
                    class_name="text-sm font-semibold text-[#e4ff9b]",
                ),
                rx.el.span(
                    f"/ {harvest['expected_yield']:.1f} t/ha",
                    class_name="text-[10px] font-medium text-[#c9c5b4]/40",
                ),
                class_name="flex items-end gap-1",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                    style={"width": harvest["performance_pct"]},
                ),
                class_name="h-1.5 w-full min-w-[6rem] rounded-none bg-[#20241a] mt-1.5",
            ),
            class_name="px-3 py-2.5 align-middle min-w-[10rem]",
        ),
        rx.el.td(
            _perf_badge(harvest["tone"], harvest["performance"]),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.p(
                harvest["quality_label"],
                class_name="text-[11px] font-semibold text-[#f2efe4] whitespace-nowrap",
            ),
            rx.el.p(
                f"H {harvest['moisture']:.1f} % · pertes {harvest['loss']:.1f} %",
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.p(
                f"{harvest['revenue']:.0f} €",
                class_name="text-xs font-semibold text-[#e4ff9b] whitespace-nowrap text-right",
            ),
            rx.el.p(
                f"{harvest['unit_price']:.0f} €/{harvest['unit']}",
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 whitespace-nowrap text-right",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.p(
                harvest["storage"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/55 truncate",
            ),
            rx.el.p(
                harvest["operator"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/35 truncate",
            ),
            class_name="px-3 py-2.5 align-middle min-w-[9rem]",
        ),
        key=key,
        class_name="border-b border-[#f2efe4]/8 even:bg-[#0d0f09] hover:bg-[#d8fa5e]/[0.05] transition-colors",
    )


def _head(label: str, extra: str = "") -> rx.Component:
    return rx.el.th(
        label,
        class_name=f"px-3 py-3 text-left ap-eyebrow text-[#c9c5b4]/45 whitespace-nowrap {extra}",
    )


def _mode_button(label: str, value: str, icon: str) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-3.5 w-3.5"),
        rx.el.span(label, class_name="text-[11px]"),
        on_click=OperationsState.set_yield_mode(value),
        class_name=rx.cond(
            OperationsState.yield_mode == value,
            "flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/15 px-3 py-1.5 font-semibold text-[#efffc4] w-fit",
            "flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1.5 font-medium text-[#c9c5b4]/55 hover:text-[#f2efe4] hover:border-[#d8fa5e]/30 transition-colors w-fit",
        ),
    )


def _yield_bar(row: YieldRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    row["label"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    row["sublabel"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/40 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                rx.cond(
                    row["delta"] >= 0,
                    f"+{row['delta']}% vs objectif",
                    f"{row['delta']}% vs objectif",
                ),
                class_name=rx.match(
                    row["tone"],
                    (
                        "good",
                        "text-[10px] font-bold text-[#e4ff9b] shrink-0 whitespace-nowrap",
                    ),
                    (
                        "warn",
                        "text-[10px] font-bold text-[#ffb894] shrink-0 whitespace-nowrap",
                    ),
                    "text-[10px] font-bold text-[#ff9b8c] shrink-0 whitespace-nowrap",
                ),
            ),
            class_name="flex items-start gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-r-full bg-gradient-to-r from-[#6e9159] to-[#d8fa5e]",
                    style={"width": row["actual_width"]},
                ),
                class_name="h-3 w-full rounded-r-full bg-[#191c13]",
            ),
            rx.el.span(
                f"{row['actual']:.1f} t/ha réalisés",
                class_name="text-[10px] font-semibold text-[#e4ff9b] w-32 shrink-0 text-right",
            ),
            class_name="flex items-center gap-3 mt-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-r-full bg-[#ff8a5b]/40 border-r-2 border-[#ff8a5b]",
                    style={"width": row["expected_width"]},
                ),
                class_name="h-2 w-full rounded-r-full bg-[#14160f]",
            ),
            rx.el.span(
                f"{row['expected']:.1f} t/ha visés",
                class_name="text-[10px] font-medium text-[#ffb894]/80 w-32 shrink-0 text-right",
            ),
            class_name="flex items-center gap-3 mt-1.5",
        ),
        rx.el.div(
            rx.icon("wheat", class_name="h-3 w-3 text-[#a9c98b]/70"),
            rx.el.span(
                f"{row['quantity']:.1f} t collectées",
                class_name="text-[10px] font-medium text-[#c9c5b4]/50",
            ),
            rx.icon("coins", class_name="h-3 w-3 text-[#ff8a5b]/70 ml-2"),
            rx.el.span(
                f"{row['revenue']:.0f} €",
                class_name="text-[10px] font-medium text-[#c9c5b4]/50",
            ),
            class_name="flex items-center gap-1.5 border-t border-[#f2efe4]/8 pt-2.5 mt-3",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors",
    )


def yield_comparison() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Performance agronomique",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Rendements réalisés vs objectifs",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _mode_button("Par parcelle", "PARCELLE", "map"),
                _mode_button("Par culture", "CULTURE", "sprout"),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(class_name="h-2 w-6 rounded-none bg-[#d8fa5e]"),
                rx.el.span(
                    "Rendement réalisé",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60",
                ),
                class_name="flex items-center gap-2 w-fit",
            ),
            rx.el.div(
                rx.el.span(class_name="h-2 w-6 rounded-none bg-[#ff8a5b]/60"),
                rx.el.span(
                    "Objectif de la fiche culturale",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60",
                ),
                class_name="flex items-center gap-2 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-5 mt-4",
        ),
        rx.cond(
            OperationsState.yield_rows.length() > 0,
            rx.el.div(
                rx.foreach(
                    OperationsState.yield_rows,
                    lambda row: _yield_bar(row, key=row["label"]),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-4 mt-5",
            ),
            rx.el.div(
                rx.icon(
                    "chart-no-axes-column", class_name="h-6 w-6 text-[#ff8a5b]"
                ),
                rx.el.p(
                    "Aucune récolte enregistrée : saisissez une première récolte pour comparer les rendements.",
                    class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2 text-center max-w-md",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-14 mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )


def harvest_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Chantiers de récolte",
                    class_name="ap-eyebrow text-[#ff8a5b]/80",
                ),
                rx.el.h2(
                    "Registre des récoltes",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{OperationsState.harvest_count} saisies",
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit",
                ),
                rx.el.button(
                    rx.icon("wheat", class_name="h-4 w-4 text-[#0A0A08]"),
                    rx.el.span(
                        "Saisir une récolte", class_name="text-[#0A0A08]"
                    ),
                    on_click=OperationsState.open_harvest_form,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        rx.cond(
            OperationsState.harvests.length() > 0,
            rx.el.div(
                rx.el.div(
                    rx.el.table(
                        rx.el.thead(
                            rx.el.tr(
                                _head("Culture"),
                                _head("Date"),
                                _head("Volume"),
                                _head("Rendement"),
                                _head("Atteinte"),
                                _head("Qualité"),
                                _head("Produit", "text-right"),
                                _head("Stockage"),
                                class_name="border-b border-[#f2efe4]/12 bg-[#101208]",
                            ),
                        ),
                        rx.el.tbody(
                            rx.foreach(
                                OperationsState.harvests,
                                lambda h: _harvest_row(
                                    h, key=h["id"].to_string()
                                ),
                            ),
                        ),
                        class_name="table-auto w-full min-w-[62rem]",
                    ),
                    class_name="overflow-x-auto",
                ),
                class_name="mt-5 w-full rounded-none border border-[#f2efe4]/12 bg-[#0D0F09]/60 overflow-hidden max-h-[32rem] overflow-y-auto",
            ),
            rx.el.div(
                rx.icon("wheat", class_name="h-6 w-6 text-[#ff8a5b]"),
                rx.el.p(
                    "Aucune récolte consignée pour le moment.",
                    class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-14 mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )
