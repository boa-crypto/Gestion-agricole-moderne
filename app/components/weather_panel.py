import reflex as rx

from app.states.weather_state import (
    WeatherDaily,
    WeatherHour,
    WeatherState,
)


def _weather_icon(kind: rx.Var, class_name: str) -> rx.Component:
    return rx.match(
        kind,
        ("sun", rx.icon("sun", class_name=class_name)),
        ("cloud-sun", rx.icon("cloud-sun", class_name=class_name)),
        ("cloud", rx.icon("cloud", class_name=class_name)),
        ("cloud-fog", rx.icon("cloud-fog", class_name=class_name)),
        ("cloud-drizzle", rx.icon("cloud-drizzle", class_name=class_name)),
        ("cloud-rain", rx.icon("cloud-rain", class_name=class_name)),
        ("snowflake", rx.icon("snowflake", class_name=class_name)),
        ("cloud-lightning", rx.icon("cloud-lightning", class_name=class_name)),
        rx.icon("cloud", class_name=class_name),
    )


def _index_tile(
    label: str, value: rx.Var | str, unit: str, icon: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]"),
            rx.el.span(
                label,
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.el.span(
                value, class_name="text-lg font-semibold text-[rgb(var(--ap-paper-rgb))]"
            ),
            rx.el.span(
                unit, class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"
            ),
            class_name="flex items-end gap-1 mt-1.5",
        ),
        class_name="w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3",
    )


def _header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Météo réelle Open-Meteo",
                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
            ),
            rx.el.h2(
                "Fenêtres d'intervention",
                class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
            ),
            rx.el.div(
                rx.icon("map-pin", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]"),
                rx.el.span(
                    WeatherState.position_source,
                    class_name="text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)]",
                ),
                rx.el.span(
                    WeatherState.coords_label,
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                rx.cond(
                    WeatherState.timezone != "",
                    rx.el.span(
                        f"· {WeatherState.timezone}",
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-2 mt-3",
            ),
            class_name="min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                WeatherState.current["date_label"],
                class_name="text-xs font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.el.div(
                rx.el.button(
                    rx.cond(
                        WeatherState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-3.5 w-3.5 animate-spin text-[rgb(var(--ap-ink-rgb))]",
                        ),
                        rx.icon(
                            "locate-fixed",
                            class_name="h-3.5 w-3.5 text-[rgb(var(--ap-ink-rgb))]",
                        ),
                    ),
                    rx.el.span(
                        "Utiliser ma position", class_name="text-[rgb(var(--ap-ink-rgb))]"
                    ),
                    on_click=WeatherState.request_geolocation,
                    class_name="flex items-center gap-2 rounded-none bg-[rgb(var(--ap-accent-rgb))] px-3.5 py-2 text-xs font-semibold hover:bg-[rgb(var(--ap-accent-soft-rgb))] transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon(
                        "refresh-cw", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]"
                    ),
                    rx.el.span(
                        "Actualiser",
                        class_name="text-xs font-semibold text-[rgb(var(--ap-paper-rgb)/0.95)]",
                    ),
                    on_click=WeatherState.load_weather,
                    class_name="flex items-center gap-2 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3.5 py-2 hover:bg-[rgb(var(--ap-surface-control-rgb))] transition-colors w-fit",
                ),
                class_name="flex items-center gap-2 mt-3",
            ),
            class_name="flex flex-col items-start md:items-end",
        ),
        class_name="flex flex-col md:flex-row md:items-start justify-between gap-4",
    )


def _now_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _weather_icon(
                WeatherState.current["kind"], "h-12 w-12 text-[rgb(var(--ap-flame-tint-rgb))]"
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        WeatherState.current["temp"],
                        class_name="ap-serif text-5xl leading-none text-[rgb(var(--ap-paper-rgb))]",
                    ),
                    rx.el.span(
                        "°C",
                        class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mb-1",
                    ),
                    class_name="flex items-end gap-1",
                ),
                rx.el.p(
                    WeatherState.current["label"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.95)]",
                ),
                rx.el.p(
                    f"Mini {WeatherState.current['tmin']} °C · Maxi {WeatherState.current['tmax']} °C · Hygro {WeatherState.current['humidity']} % · Vent {WeatherState.current['wind']} km/h (raf. {WeatherState.current['gust']})",
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1",
                ),
                rx.el.p(
                    f"Lever {WeatherState.current['sunrise']} · Coucher {WeatherState.current['sunset']} · Pluie prévue {WeatherState.current['rain']} mm ({WeatherState.current['rain_prob']} %)",
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-0.5",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-center gap-5",
        ),
        rx.el.div(
            rx.cond(
                WeatherState.current["spray_tone"] == "good",
                rx.icon("spray-can", class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
                rx.icon("wind", class_name="h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]"),
            ),
            rx.el.span(
                WeatherState.current["spray_label"],
                class_name=rx.cond(
                    WeatherState.current["spray_tone"] == "good",
                    "text-xs font-semibold text-[rgb(var(--ap-accent-soft-rgb))]",
                    "text-xs font-semibold text-[rgb(var(--ap-flame-tint-rgb))]",
                ),
            ),
            class_name=rx.cond(
                WeatherState.current["spray_tone"] == "good",
                "flex items-center gap-2 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-3 py-1.5 w-fit h-fit",
                "flex items-center gap-2 rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-3 py-1.5 w-fit h-fit",
            ),
        ),
        class_name="flex flex-col md:flex-row md:items-center justify-between gap-4 mt-6",
    )


def _hour_cell(hour: WeatherHour) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            hour["hour"],
            class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.78)]",
        ),
        _weather_icon(hour["kind"], "h-4 w-4 text-[rgb(var(--ap-flame-tint-rgb))] my-1.5"),
        rx.el.span(
            f"{hour['temp']:.0f}°",
            class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))]",
        ),
        rx.el.div(
            rx.icon("droplet", class_name="h-2.5 w-2.5 text-[rgb(var(--ap-info-rgb))]"),
            rx.el.span(
                f"{hour['rain']:.1f}",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-info-soft-rgb)/0.80)]",
            ),
            class_name="flex items-center gap-1 mt-1.5",
        ),
        rx.el.span(
            f"{hour['humidity']:.0f} %",
            class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
        ),
        rx.el.div(
            rx.icon("wind", class_name="h-2.5 w-2.5 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"),
            rx.el.span(
                f"{hour['wind']:.0f}",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            class_name="flex items-center gap-1 mt-1",
        ),
        title=hour["label"],
        class_name=rx.cond(
            hour["is_now"],
            "flex flex-col items-center shrink-0 w-[4.75rem] rounded-none border border-[rgb(var(--ap-accent-rgb)/0.50)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-3",
            "flex flex-col items-center shrink-0 w-[4.75rem] rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] px-2 py-3",
        ),
    )


def _hourly_rail() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("clock", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]"),
                rx.el.span(
                    "Ruban horaire du jour",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.78)]",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.span(
                f"{WeatherState.hourly.length()} heures",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            class_name="flex items-center justify-between",
        ),
        rx.cond(
            WeatherState.hourly.length() > 0,
            rx.el.div(
                rx.foreach(WeatherState.hourly, _hour_cell),
                class_name="flex gap-2 overflow-x-auto pb-2 mt-3",
            ),
            rx.el.p(
                "Aucune donnée horaire disponible.",
                class_name="text-xs font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-3",
            ),
        ),
        class_name="mt-6",
    )


def _daily_cell(day: WeatherDaily) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                day["day"],
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.78)]",
            ),
            rx.el.span(
                day["date_label"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
            ),
            class_name="flex flex-col items-center",
        ),
        _weather_icon(day["kind"], "h-5 w-5 text-[rgb(var(--ap-flame-tint-rgb))] my-2"),
        rx.el.div(
            rx.el.span(
                f"{day['tmax']:.0f}°",
                class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))]",
            ),
            rx.el.span(
                f"{day['tmin']:.0f}°",
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            class_name="flex items-baseline gap-1.5",
        ),
        rx.el.div(
            rx.icon("droplet", class_name="h-3 w-3 text-[rgb(var(--ap-info-rgb))]"),
            rx.el.span(
                f"{day['rain']:.1f}",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-info-soft-rgb)/0.80)]",
            ),
            rx.el.span(
                f"{day['rain_prob']:.0f}%",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            class_name="flex items-center gap-1 mt-2",
        ),
        rx.el.div(
            rx.icon("wind", class_name="h-3 w-3 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"),
            rx.el.span(
                f"{day['wind']:.0f} km/h",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            class_name="flex items-center gap-1 mt-1",
        ),
        rx.cond(
            day["spray"],
            rx.el.span(
                "Traitement OK",
                class_name="mt-2 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-1.5 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
            ),
            rx.el.span(
                "Traitement NON",
                class_name="mt-2 rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.40)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-1.5 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
            ),
        ),
        title=day["label"],
        class_name=rx.cond(
            day["is_today"],
            "flex flex-col items-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-accent-rgb))]/[0.07] px-2 py-3 w-full",
            "flex flex-col items-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] px-2 py-3 w-full",
        ),
    )


def _daily_grid() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("calendar-range", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]"),
            rx.el.span(
                "Horizon 15 jours",
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.78)]",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.foreach(WeatherState.daily, _daily_cell),
            class_name="grid grid-cols-3 sm:grid-cols-5 xl:grid-cols-8 gap-2 mt-3",
        ),
        class_name="mt-6",
    )


def weather_panel() -> rx.Component:
    return rx.el.section(
        _header(),
        rx.cond(
            WeatherState.error != "",
            rx.el.div(
                rx.icon(
                    "triangle-alert", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-flame-soft-rgb))]"
                ),
                rx.el.span(
                    WeatherState.error,
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-flame-tint-rgb))]",
                ),
                class_name="flex items-center gap-2 rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-3 py-2 mt-4",
            ),
            rx.fragment(),
        ),
        rx.cond(
            WeatherState.is_simulated,
            rx.el.span(
                "Données simulées de secours",
                class_name="mt-4 inline-flex rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-1 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            rx.fragment(),
        ),
        _now_block(),
        rx.el.div(
            _index_tile(
                "ET0 (FAO)", WeatherState.current["et0"], "mm/j", "sun-dim"
            ),
            _index_tile(
                "Humidité du sol",
                WeatherState.current["soil"],
                "%",
                "waves",
            ),
            _index_tile(
                "Degrés-jours",
                WeatherState.current["gdd"],
                "°C.j",
                "thermometer",
            ),
            _index_tile(
                "Pluie 7 jours",
                WeatherState.current["rain_week"],
                "mm",
                "cloud-rain",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-6",
        ),
        _hourly_rail(),
        _daily_grid(),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )
