import reflex as rx

from app.states.guide_state import FaqCard, GuideState


def _faq_row(item: FaqCard, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.el.div(
                rx.icon(
                    "message-circle-question",
                    class_name="h-4 w-4 text-[#d8fa5e]",
                ),
                class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
            ),
            rx.el.div(
                rx.el.p(
                    item["question"],
                    class_name="text-sm font-semibold text-[#f2efe4] text-left",
                ),
                rx.el.div(
                    rx.el.span(
                        item["category_name"],
                        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/55 w-fit",
                    ),
                    rx.el.span(
                        item["audience_label"],
                        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/55 w-fit",
                    ),
                    rx.cond(
                        item["is_frequent"],
                        rx.el.span(
                            "Fréquente",
                            class_name="rounded-none border border-[#ff8a5b]/35 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit",
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-2",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.icon(
                "chevron-down",
                class_name=rx.cond(
                    GuideState.open_faq_id == item["id"],
                    "h-4 w-4 text-[#d8fa5e] rotate-180 transition-transform shrink-0",
                    "h-4 w-4 text-[#c9c5b4]/45 transition-transform shrink-0",
                ),
            ),
            on_click=GuideState.toggle_faq(item["id"]),
            class_name="flex items-start gap-3 w-full text-left",
        ),
        rx.cond(
            GuideState.open_faq_id == item["id"],
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        "Réponse agricole",
                        class_name="ap-eyebrow text-[#d8fa5e]/70",
                    ),
                    rx.el.p(
                        item["answer_farmer"],
                        class_name="text-[12px] font-medium text-[#c9c5b4]/70 leading-relaxed mt-1",
                    ),
                    class_name="flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
                ),
                rx.el.div(
                    rx.el.span(
                        "Réponse AgriPro",
                        class_name="ap-eyebrow text-[#ff8a5b]/70",
                    ),
                    rx.el.p(
                        item["answer_pro"],
                        class_name="text-[12px] font-medium text-[#c9c5b4]/70 leading-relaxed mt-1",
                    ),
                    class_name="flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
                ),
                rx.cond(
                    item["module_route"] != "",
                    rx.el.a(
                        rx.el.span("Ouvrir l'écran concerné"),
                        rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
                        href=item["module_route"],
                        class_name="flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10 px-3 py-1.5 text-[11px] font-semibold text-[#e4ff9b] hover:bg-[#d8fa5e]/20 transition-colors w-fit shrink-0 self-end",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-col lg:flex-row gap-2 w-full mt-4 pt-4 border-t border-[#f2efe4]/8",
            ),
            rx.fragment(),
        ),
        key=key,
        class_name=rx.cond(
            GuideState.open_faq_id == item["id"],
            "w-full rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/[0.05] p-4",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors",
        ),
    )


def guide_faq() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "FAQ intelligente",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Les questions posées sur le terrain",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    f"Périmètre : {GuideState.category_label}",
                    class_name="ap-eyebrow text-[#c9c5b4]/40 mt-2",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{GuideState.frequent_questions.length()} fréquente(s)",
                    class_name="rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-3 py-1 text-[11px] font-semibold text-[#ffb894] w-fit",
                ),
                rx.el.span(
                    f"{GuideState.visible_faq.length()} affichée(s)",
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/65 w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            GuideState.visible_faq.length() > 0,
            rx.el.div(
                rx.foreach(
                    GuideState.visible_faq,
                    lambda item: _faq_row(item, key=item["id"].to_string()),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-5",
            ),
            rx.el.div(
                rx.icon("search-x", class_name="h-6 w-6 text-[#ff8a5b]"),
                rx.el.p(
                    "Aucune question pour cette catégorie.",
                    class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-12 w-full mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )
