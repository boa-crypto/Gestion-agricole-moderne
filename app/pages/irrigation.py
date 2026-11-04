import reflex as rx

from app.components.irrigation import irrigation_header, irrigation_workspace
from app.components.side_rail import side_rail


def irrigation_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            side_rail("irrigation"),
            irrigation_header(),
            irrigation_workspace(),
            class_name="w-full min-w-0 px-4 sm:px-8 md:pl-24 lg:pl-28 xl:pl-72 py-10 pb-28 md:pb-10",
        ),
        class_name="min-h-screen w-full bg-[#04120c] text-emerald-50 font-['Inter'] antialiased",
    )
