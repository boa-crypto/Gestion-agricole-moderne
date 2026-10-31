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
from app.components.shell import app_shell
from app.states.guide_state import GuideState


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="animate-pulse h-40 rounded-none bg-[#16190f]"),
        rx.el.div(class_name="animate-pulse h-64 rounded-none bg-[#16190f]"),
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
    return app_shell(
        rx.el.div(
            guide_hero(),
            rx.el.div(
                guide_sections(),
                guide_categories(),
                rx.cond(GuideState.is_loading, _skeleton(), _body()),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            class_name="flex w-full flex-col gap-6",
        ),
        "guide",
    )
