import reflex as rx

from app.components.guide_admin import guide_admin
from app.components.guide_dictionary import guide_dictionary
from app.components.guide_faq import guide_faq
from app.components.guide_hero import guide_hero
from app.components.guide_library import guide_library
from app.components.guide_nav import guide_categories, guide_sections
from app.components.guide_paths import guide_paths
from app.components.guide_relations import guide_relations
from app.components.guide_rules import guide_rules
from app.components.side_rail import side_rail
from app.states.guide_state import GuideState


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="animate-pulse h-40 rounded-3xl bg-white/[0.05]"),
        rx.el.div(class_name="animate-pulse h-64 rounded-3xl bg-white/[0.05]"),
        class_name="flex flex-col gap-4 w-full",
    )


def _body() -> rx.Component:
    return rx.match(
        GuideState.active_section,
        ("bibliotheque", guide_library()),
        ("dictionnaire", guide_dictionary()),
        ("faq", guide_faq()),
        ("parcours", guide_paths()),
        ("regles", guide_rules()),
        ("relations", guide_relations()),
        ("administration", guide_admin()),
        guide_library(),
    )


def guide_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            class_name="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-[#04120c]/35 via-[#04120c]/45 to-[#020a07]/60",
        ),
        rx.el.div(
            side_rail("guide"),
            guide_hero(),
            rx.el.div(
                guide_sections(),
                guide_categories(),
                rx.cond(GuideState.is_loading, _skeleton(), _body()),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            class_name="relative z-10 w-full max-w-[110rem] mx-auto px-4 sm:px-8 md:pl-24 lg:pl-28 py-10 pb-28 md:pb-10",
        ),
        class_name="relative min-h-screen w-full font-['Inter'] bg-[#04120c] bg-[url('/wide_cinematic_background.png')] bg-cover bg-center bg-fixed text-emerald-50 antialiased",
    )
