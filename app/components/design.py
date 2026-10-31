"""Système de design « Ivoire & Bronze » d'AgriPro.

Direction artistique : maison d'hôtellerie de standing, reprise pour un outil
agricole. Ivoire chaud en fond, encre profonde pour la lecture, bronze pour les
filets d'accent, angles vifs, typographie d'apparat (Cormorant Garamond pour le
registre éditorial, Inter Tight pour la lecture, JetBrains Mono réservée aux
données chiffrées) et animations lentes.

Deux thèmes partagent le même jeu de jetons : « ivoire » par défaut et
« encre » (l'ancienne palette chlorophylle) pour les écrans en lumière basse.
Le basculement se fait par l'attribut `data-theme` posé sur `<html>`.

Le module centralise les jetons (couleurs, typographies, filets) et expose les
primitives réutilisées par la coque applicative et les en-têtes de section.
"""

from __future__ import annotations

import reflex as rx

# ---------------------------------------------------------------------------
# Jetons
# ---------------------------------------------------------------------------

INK = "rgb(var(--ap-ink-rgb))"
INK_DEEP = "rgb(var(--ap-ink-deep-rgb))"
SURFACE = "rgb(var(--ap-surface-rgb))"
SURFACE_RAISED = "rgb(var(--ap-surface-raised-rgb))"
SURFACE_HIGH = "rgb(var(--ap-surface-high-rgb))"
SURFACE_CONTROL = "rgb(var(--ap-surface-control-rgb))"
PAPER = "rgb(var(--ap-paper-rgb))"
PAPER_MUTED = "rgb(var(--ap-paper-muted-rgb))"
PAPER_FAINT = "rgb(var(--ap-paper-faint-rgb))"
ACCENT = "rgb(var(--ap-accent-rgb))"
ACCENT_DEEP = "rgb(var(--ap-accent-deep-rgb))"
BRONZE = "rgb(var(--ap-bronze-rgb))"
BRONZE_LIGHT = "rgb(var(--ap-bronze-light-rgb))"
FLAME = "rgb(var(--ap-flame-rgb))"
FLAME_SOFT = "rgb(var(--ap-flame-soft-rgb))"
SAGE = "rgb(var(--ap-sage-rgb))"
INFO = "rgb(var(--ap-info-rgb))"
DANGER = "rgb(var(--ap-danger-rgb))"

FONT_DISPLAY = "ap-serif"
FONT_SANS = "font-['Inter_Tight']"
FONT_MONO = "font-['JetBrains_Mono']"

LINE = "border-[rgb(var(--ap-paper-rgb)/0.18)]"
LINE_SOFT = "border-[rgb(var(--ap-paper-rgb)/0.12)]"
LINE_STRONG = "border-[rgb(var(--ap-paper-rgb)/0.30)]"

GOOGLE_FONTS_HREF = (
    "https://fonts.googleapis.com/css2"
    "?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400"
    "&family=Inter+Tight:wght@300;400;500;600"
    "&family=JetBrains+Mono:wght@400;500"
    "&display=swap"
)

# ---------------------------------------------------------------------------
# Feuille de style globale
# ---------------------------------------------------------------------------

GLOBAL_CSS = """
/* ---------------------------------------------------------------------------
   Jetons de charte — « Park Lane » : ivoire, encre et bronze.
   Les couleurs sont stockées en canaux RVB pour que Tailwind puisse leur
   appliquer une opacité : rgb(var(--ap-paper-rgb)/0.12).
   --------------------------------------------------------------------------- */

:root {
  color-scheme: light;
  --ap-accent-deep-rgb: 44 42 32;
  --ap-accent-mid-rgb: 50 47 36;
  --ap-accent-olive-rgb: 93 86 54;
  --ap-accent-pale-rgb: 58 55 43;
  --ap-accent-rgb: 27 26 20;
  --ap-accent-soft-rgb: 74 70 54;
  --ap-accent-wash-rgb: 66 62 46;
  --ap-bark-rgb: 107 74 48;
  --ap-blue-700-rgb: 29 78 216;
  --ap-bronze-deep-rgb: 138 96 42;
  --ap-bronze-light-rgb: 176 128 58;
  --ap-bronze-rgb: 150 112 60;
  --ap-danger-base-rgb: 176 68 61;
  --ap-danger-brick-rgb: 156 60 69;
  --ap-danger-crimson-rgb: 168 50 74;
  --ap-danger-deep-rgb: 143 43 43;
  --ap-danger-flat-rgb: 176 74 66;
  --ap-danger-pale-rgb: 180 103 103;
  --ap-danger-rgb: 176 65 47;
  --ap-danger-rose-rgb: 168 63 78;
  --ap-danger-soft-rgb: 168 90 73;
  --ap-danger-wine-rgb: 125 44 64;
  --ap-flame-rgb: 168 63 33;
  --ap-flame-soft-rgb: 164 85 44;
  --ap-flame-strong-rgb: 168 58 34;
  --ap-flame-tint-rgb: 192 122 78;
  --ap-forest-rgb: 20 83 45;
  --ap-fuchsia-pale-rgb: 230 205 240;
  --ap-fuchsia-rgb: 161 79 176;
  --ap-indigo-300-rgb: 107 118 174;
  --ap-indigo-400-rgb: 91 99 176;
  --ap-info-pale-rgb: 215 226 238;
  --ap-info-rgb: 70 101 138;
  --ap-info-soft-rgb: 63 92 125;
  --ap-ink-deep-rgb: 253 252 249;
  --ap-ink-rgb: 247 244 236;
  --ap-mint-050-rgb: 236 253 245;
  --ap-moss-rgb: 240 248 242;
  --ap-neutral-deep-rgb: 128 122 106;
  --ap-paper-bright-rgb: 42 40 32;
  --ap-paper-faint-rgb: 102 98 88;
  --ap-paper-muted-rgb: 72 69 60;
  --ap-paper-rgb: 26 25 18;
  --ap-paper-soft-rgb: 116 111 99;
  --ap-rose-deep-rgb: 168 85 97;
  --ap-rose-rgb: 168 84 122;
  --ap-sage-deep-rgb: 79 98 66;
  --ap-sage-deeper-rgb: 67 84 54;
  --ap-sage-rgb: 95 115 80;
  --ap-sage-soft-rgb: 92 111 78;
  --ap-sand-deep-rgb: 145 105 74;
  --ap-sand-rgb: 150 112 60;
  --ap-sky-200-rgb: 84 116 152;
  --ap-sky-300-rgb: 84 116 152;
  --ap-sky-400-rgb: 74 104 140;
  --ap-sky-500-rgb: 51 106 138;
  --ap-slate-200-rgb: 229 231 235;
  --ap-slate-300-rgb: 203 210 218;
  --ap-slate-500-rgb: 100 116 139;
  --ap-slate-800-rgb: 31 41 55;
  --ap-surface-control-rgb: 226 218 202;
  --ap-surface-faint-rgb: 248 245 237;
  --ap-surface-high-rgb: 233 227 213;
  --ap-surface-muted-rgb: 239 234 223;
  --ap-surface-raised-rgb: 241 236 226;
  --ap-surface-rgb: 250 248 241;
  --ap-surface-soft-rgb: 249 246 239;
  --ap-teal-200-rgb: 94 234 212;
  --ap-teal-400-rgb: 45 212 191;
  --ap-teal-600-rgb: 13 148 136;
  --ap-terra-rgb: 168 96 47;
  --ap-track-deep-rgb: 203 193 173;
  --ap-track-rgb: 214 205 187;
  --ap-track-soft-rgb: 222 214 199;
  --ap-violet-300-rgb: 122 108 176;
  --ap-violet-900-rgb: 74 42 102;
  --ap-violet-pale-rgb: 214 205 240;
  --ap-violet-rgb: 99 84 176;
  --ap-violet-soft-rgb: 122 106 158;
  --ap-warm-050-rgb: 235 211 204;
  --ap-warm-100-rgb: 232 205 185;
  --ap-warm-150-rgb: 227 188 174;
  --ap-warm-200-rgb: 185 103 63;
  --ap-warm-225-rgb: 233 215 186;
  --ap-warm-250-rgb: 224 195 168;
  --ap-warm-300-rgb: 169 122 47;
  --ap-warm-325-rgb: 232 211 162;
  --ap-warm-350-rgb: 236 217 174;
  --ap-warm-400-rgb: 168 74 36;
  --ap-line: rgb(var(--ap-paper-rgb) / 0.14);
  --ap-line-soft: rgb(var(--ap-paper-rgb) / 0.08);
  --ap-line-strong: rgb(var(--ap-paper-rgb) / 0.26);
  --ap-serif: 'Cormorant Garamond', 'Instrument Serif', 'Times New Roman', Georgia, serif;
  --ap-sans: 'Inter Tight', 'Inter', system-ui, -apple-system, sans-serif;
  --ap-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  --ap-ease: cubic-bezier(.16, .84, .44, 1);
}

/* Variante sombre : encre et chlorophylle, conservée à l'identique. */
[data-theme="dark"] {
  color-scheme: dark;
  --ap-accent-deep-rgb: 182 217 63;
  --ap-accent-mid-rgb: 194 232 71;
  --ap-accent-olive-rgb: 147 174 69;
  --ap-accent-pale-rgb: 239 255 196;
  --ap-accent-rgb: 216 250 94;
  --ap-accent-soft-rgb: 228 255 155;
  --ap-accent-wash-rgb: 217 249 157;
  --ap-bark-rgb: 63 36 21;
  --ap-blue-700-rgb: 29 78 216;
  --ap-bronze-deep-rgb: 169 118 47;
  --ap-bronze-light-rgb: 240 168 74;
  --ap-bronze-rgb: 196 146 60;
  --ap-danger-base-rgb: 239 68 68;
  --ap-danger-brick-rgb: 195 58 70;
  --ap-danger-crimson-rgb: 225 29 72;
  --ap-danger-deep-rgb: 185 28 28;
  --ap-danger-flat-rgb: 248 113 113;
  --ap-danger-pale-rgb: 252 165 165;
  --ap-danger-rgb: 255 107 90;
  --ap-danger-rose-rgb: 244 63 94;
  --ap-danger-soft-rgb: 255 155 140;
  --ap-danger-wine-rgb: 159 18 57;
  --ap-flame-rgb: 255 90 43;
  --ap-flame-soft-rgb: 255 138 91;
  --ap-flame-strong-rgb: 242 69 44;
  --ap-flame-tint-rgb: 255 184 148;
  --ap-forest-rgb: 20 83 45;
  --ap-fuchsia-pale-rgb: 245 208 254;
  --ap-fuchsia-rgb: 232 121 249;
  --ap-indigo-300-rgb: 165 180 252;
  --ap-indigo-400-rgb: 129 140 248;
  --ap-info-pale-rgb: 226 236 255;
  --ap-info-rgb: 156 195 255;
  --ap-info-soft-rgb: 195 218 255;
  --ap-ink-deep-rgb: 6 6 4;
  --ap-ink-rgb: 10 10 8;
  --ap-mint-050-rgb: 236 253 245;
  --ap-moss-rgb: 6 23 15;
  --ap-neutral-deep-rgb: 74 81 64;
  --ap-paper-bright-rgb: 232 230 220;
  --ap-paper-faint-rgb: 143 140 126;
  --ap-paper-muted-rgb: 201 197 180;
  --ap-paper-rgb: 242 239 228;
  --ap-paper-soft-rgb: 179 175 159;
  --ap-rose-deep-rgb: 255 147 161;
  --ap-rose-rgb: 255 158 201;
  --ap-sage-deep-rgb: 110 145 89;
  --ap-sage-deeper-rgb: 85 118 68;
  --ap-sage-rgb: 169 201 139;
  --ap-sage-soft-rgb: 143 179 122;
  --ap-sand-deep-rgb: 176 137 104;
  --ap-sand-rgb: 212 163 115;
  --ap-sky-200-rgb: 125 211 252;
  --ap-sky-300-rgb: 147 197 253;
  --ap-sky-400-rgb: 96 165 250;
  --ap-sky-500-rgb: 14 165 233;
  --ap-slate-200-rgb: 229 231 235;
  --ap-slate-300-rgb: 203 213 225;
  --ap-slate-500-rgb: 100 116 139;
  --ap-slate-800-rgb: 31 41 55;
  --ap-surface-control-rgb: 32 36 26;
  --ap-surface-faint-rgb: 15 17 10;
  --ap-surface-high-rgb: 25 28 19;
  --ap-surface-muted-rgb: 22 25 15;
  --ap-surface-raised-rgb: 20 22 15;
  --ap-surface-rgb: 16 18 8;
  --ap-surface-soft-rgb: 13 15 9;
  --ap-teal-200-rgb: 94 234 212;
  --ap-teal-400-rgb: 45 212 191;
  --ap-teal-600-rgb: 13 148 136;
  --ap-terra-rgb: 222 114 51;
  --ap-track-deep-rgb: 51 57 39;
  --ap-track-rgb: 43 48 32;
  --ap-track-soft-rgb: 44 49 35;
  --ap-violet-300-rgb: 196 181 253;
  --ap-violet-900-rgb: 88 28 135;
  --ap-violet-pale-rgb: 211 198 255;
  --ap-violet-rgb: 142 123 255;
  --ap-violet-soft-rgb: 185 168 255;
  --ap-warm-050-rgb: 255 224 218;
  --ap-warm-100-rgb: 255 220 203;
  --ap-warm-150-rgb: 255 188 176;
  --ap-warm-200-rgb: 255 158 122;
  --ap-warm-225-rgb: 255 228 196;
  --ap-warm-250-rgb: 255 201 168;
  --ap-warm-300-rgb: 255 196 107;
  --ap-warm-325-rgb: 255 223 155;
  --ap-warm-350-rgb: 255 233 184;
  --ap-warm-400-rgb: 255 106 56;
}

/* Filet de sécurité : les familles Tailwind héritées suivent la charte. */
:root {
  --color-lime-100: rgb(var(--ap-accent-pale-rgb));
  --color-lime-200: rgb(var(--ap-accent-soft-rgb));
  --color-lime-300: rgb(var(--ap-accent-rgb));
  --color-lime-400: rgb(var(--ap-accent-mid-rgb));
  --color-emerald-50: rgb(var(--ap-paper-rgb));
  --color-emerald-100: rgb(var(--ap-paper-muted-rgb));
  --color-emerald-300: rgb(var(--ap-sage-rgb));
  --color-amber-200: rgb(var(--ap-flame-tint-rgb));
  --color-amber-300: rgb(var(--ap-flame-soft-rgb));
  --color-red-300: rgb(var(--ap-danger-soft-rgb));
  --color-red-400: rgb(var(--ap-danger-rgb));
  --color-sky-300: rgb(var(--ap-info-rgb));
  --color-white: rgb(var(--ap-paper-rgb));
}

html {
  background-color: rgb(var(--ap-ink-rgb));
  -webkit-text-size-adjust: 100%;
}

body {
  background-color: rgb(var(--ap-ink-rgb));
  color: rgb(var(--ap-paper-rgb));
  font-family: var(--ap-sans);
  letter-spacing: -0.012em;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

/* Grain d'impression, très discret, au-dessus des surfaces. */
body::after {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 25;
  pointer-events: none;
  opacity: 0.035;
  mix-blend-mode: soft-light;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)' opacity='0.55'/%3E%3C/svg%3E");
}

::selection {
  background: rgb(var(--ap-accent-rgb));
  color: rgb(var(--ap-ink-rgb));
}

:focus-visible {
  outline: 1px solid rgb(var(--ap-accent-rgb));
  outline-offset: 3px;
}

* {
  scrollbar-width: thin;
  scrollbar-color: rgb(var(--ap-track-rgb)) rgb(var(--ap-ink-rgb));
}

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: rgb(var(--ap-ink-rgb)); }
::-webkit-scrollbar-thumb {
  background: rgb(var(--ap-track-rgb));
  border: 3px solid rgb(var(--ap-ink-rgb));
}

h1, h2, h3, h4 { text-wrap: balance; }
p { text-wrap: pretty; }

table, .ap-tabular { font-variant-numeric: tabular-nums; }

input, select, textarea { font-family: var(--ap-sans); }

/* Primitives éditoriales -------------------------------------------------- */

/* Chiffres et micro-libellés : la grotesque tabulaire remplace le monospace,
   plus proche du registre hôtelier que du registre technique. */
.ap-mono {
  font-family: var(--ap-sans);
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum' 1;
  letter-spacing: 0.02em;
}

.ap-figure {
  font-variant-numeric: tabular-nums lining-nums;
  letter-spacing: -0.01em;
}

.ap-serif {
  font-family: var(--ap-serif);
  font-weight: 300;
  letter-spacing: -0.008em;
  font-feature-settings: 'kern' 1, 'liga' 1;
}

.ap-eyebrow {
  font-family: var(--ap-sans);
  font-size: 10px;
  font-weight: 500;
  line-height: 1;
  letter-spacing: 0.34em;
  text-transform: uppercase;
  font-feature-settings: 'tnum' 1;
}

.ap-display {
  font-family: var(--ap-serif);
  font-weight: 300;
  letter-spacing: -0.014em;
  line-height: 0.92;
  text-wrap: balance;
}

.ap-italic { font-style: italic; }

.ap-underlink {
  text-decoration: none;
  background-image: linear-gradient(currentColor, currentColor);
  background-size: 100% 1px;
  background-position: 0 100%;
  background-repeat: no-repeat;
  transition: background-size 240ms cubic-bezier(.2, .7, .2, 1);
}
.ap-underlink:hover { background-size: 0% 1px; }

.ap-hairline { border-color: rgb(var(--ap-line-rgb)); }

/* Bascule de thème -------------------------------------------------------- */

.ap-theme-light { display: inline-flex; }
.ap-theme-dark { display: none; }
html[data-theme="dark"] .ap-theme-light { display: none; }
html[data-theme="dark"] .ap-theme-dark { display: inline-flex; }

/* Micro-interactions ------------------------------------------------------ */

.ap-lift {
  transition: border-color 200ms ease, background-color 200ms ease,
    transform 260ms cubic-bezier(.2, .7, .2, 1);
}

@keyframes ap-rise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: none; }
}

@keyframes ap-fade-soft {
  from { opacity: 0; }
  to { opacity: 1; }
}

.ap-reveal { animation: ap-rise 900ms var(--ap-ease) both; }
.ap-fade { animation: ap-fade-soft 1100ms var(--ap-ease) both; }

/* Filet qui se trace sous les liens de navigation. */
.ap-link {
  position: relative;
  text-decoration: none;
}
.ap-link::after {
  content: "";
  position: absolute;
  left: 0;
  bottom: -4px;
  height: 1px;
  width: 100%;
  background: currentColor;
  transform: scaleX(0);
  transform-origin: left center;
  transition: transform 420ms var(--ap-ease);
}
.ap-link:hover::after,
.ap-link:focus-visible::after { transform: scaleX(1); }

/* Zoom lent des visuels (cartes, aperçus cartographiques). */
.ap-zoom { overflow: hidden; }
.ap-zoom > * {
  transition: transform 900ms var(--ap-ease), filter 900ms var(--ap-ease);
}
.ap-zoom:hover > * { transform: scale(1.035); }

@keyframes ap-marquee {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}

/* Séquences d'apparition ------------------------------------------------ */

.ap-stagger > * {
  animation: ap-rise 820ms var(--ap-ease) both;
}
.ap-stagger > *:nth-child(1) { animation-delay: 0ms; }
.ap-stagger > *:nth-child(2) { animation-delay: 70ms; }
.ap-stagger > *:nth-child(3) { animation-delay: 140ms; }
.ap-stagger > *:nth-child(4) { animation-delay: 210ms; }
.ap-stagger > *:nth-child(5) { animation-delay: 280ms; }
.ap-stagger > *:nth-child(6) { animation-delay: 350ms; }
.ap-stagger > *:nth-child(7) { animation-delay: 420ms; }
.ap-stagger > *:nth-child(8) { animation-delay: 490ms; }
.ap-stagger > *:nth-child(9) { animation-delay: 560ms; }
.ap-stagger > *:nth-child(10) { animation-delay: 630ms; }
.ap-stagger > *:nth-child(n+11) { animation-delay: 700ms; }

/* Retour au clic -------------------------------------------------------- */

.ap-press {
  transition: transform 140ms cubic-bezier(.2, .7, .2, 1),
    background-color 200ms ease, border-color 200ms ease, color 200ms ease;
}
.ap-press:active { transform: translateY(1px); }

/* Affordance globale des contrôles ------------------------------------- */

button:not(:disabled),
a[role="button"] {
  transition: transform 140ms cubic-bezier(.2, .7, .2, 1),
    background-color 200ms ease, border-color 200ms ease, color 200ms ease,
    opacity 200ms ease;
}

button:not(:disabled):active,
a[role="button"]:active {
  transform: translateY(1px);
}

button:disabled { opacity: 0.45; cursor: not-allowed; }

/* Panneaux et lignes ---------------------------------------------------- */

.ap-panel { transition: border-color 200ms ease, background-color 200ms ease; }
.ap-panel:hover { border-color: rgb(var(--ap-paper-rgb) / 0.22); }

.ap-row { transition: background-color 160ms ease, color 160ms ease; }
.ap-row:hover { background-color: rgb(var(--ap-paper-rgb) / 0.04); }

/* Squelettes : balayage d'encre, pas de gris générique ------------------ */

@keyframes ap-sweep {
  0% { opacity: 0.55; background-position: 180% 0; }
  50% { opacity: 0.9; background-position: 60% 0; }
  100% { opacity: 0.55; background-position: -60% 0; }
}

.ap-skeleton,
.animate-pulse {
  background-image: linear-gradient(
    90deg,
    rgb(var(--ap-paper-rgb) / 0) 0%,
    rgb(var(--ap-paper-rgb) / 0.07) 45%,
    rgb(var(--ap-paper-rgb) / 0) 100%
  );
  background-size: 220% 100%;
  background-repeat: no-repeat;
  animation: ap-sweep 1.7s cubic-bezier(.4, 0, .2, 1) infinite !important;
}

/* Superpositions : modales, panneaux, notifications --------------------- */

@keyframes ap-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes ap-sheet {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}

@keyframes ap-toast {
  from { opacity: 0; transform: translateY(-6px); }
  to { opacity: 1; transform: none; }
}

.ap-overlay { animation: ap-fade 180ms ease-out both; }
.ap-sheet { animation: ap-sheet 260ms cubic-bezier(.2, .7, .2, 1) both; }
.ap-toast { animation: ap-toast 220ms cubic-bezier(.2, .7, .2, 1) both; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}
"""


THEME_BOOTSTRAP = """
(function () {
  var STORAGE_KEY = 'agripro-theme';
  var root = document.documentElement;
  var stored = null;
  try { stored = window.localStorage.getItem(STORAGE_KEY); } catch (e) { stored = null; }
  root.setAttribute('data-theme', stored === 'dark' ? 'dark' : 'light');
  window.agriproToggleTheme = function () {
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { window.localStorage.setItem(STORAGE_KEY, next); } catch (e) {}
  };
})();
"""


def theme_toggle() -> rx.Component:
    """Bascule ivoire / encre, sans rechargement ni état serveur."""
    return rx.el.button(
        rx.icon("moon", class_name="ap-theme-light h-3.5 w-3.5"),
        rx.icon("sun", class_name="ap-theme-dark h-3.5 w-3.5"),
        on_click=rx.call_script(
            "window.agriproToggleTheme && window.agriproToggleTheme()"
        ),
        type="button",
        aria_label="Basculer entre le thème ivoire et le thème encre",
        title="Thème ivoire / encre",
        class_name=(
            "flex h-8 w-8 items-center justify-center border "
            "border-[rgb(var(--ap-paper-rgb)/0.18)] "
            "text-[rgb(var(--ap-paper-muted-rgb))] "
            "hover:border-[rgb(var(--ap-paper-rgb)/0.30)] "
            "hover:text-[rgb(var(--ap-paper-rgb))] transition-colors"
        ),
    )


def editorial_styles() -> rx.Component:
    """Feuille de style globale injectée dans le <head> de l'application."""
    return rx.el.style(GLOBAL_CSS)


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


def eyebrow(
    text: rx.Var | str,
    *,
    tone: str = "muted",
    class_name: str = "",
) -> rx.Component:
    """Sur-titre mono, précédé d'un carré d'accent (marqueur de maison)."""
    tone_class = {
        "accent": "text-[rgb(var(--ap-accent-rgb))]",
        "flame": "text-[rgb(var(--ap-flame-soft-rgb))]",
        "paper": "text-[rgb(var(--ap-paper-rgb))]",
        "muted": "text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
    }[tone]
    dot_class = {
        "accent": "bg-[rgb(var(--ap-accent-rgb))]",
        "flame": "bg-[rgb(var(--ap-flame-rgb))]",
        "paper": "bg-[rgb(var(--ap-paper-rgb))]",
        "muted": "bg-[rgb(var(--ap-paper-muted-rgb)/0.40)]",
    }[tone]
    return rx.el.p(
        rx.el.span("", class_name=f"inline-block h-1.5 w-1.5 {dot_class}"),
        rx.el.span(text),
        class_name=f"ap-eyebrow flex items-center gap-2.5 {tone_class} {class_name}",
    )


def hairline(class_name: str = "") -> rx.Component:
    return rx.el.div(
        class_name=f"h-px w-full bg-[rgb(var(--ap-paper-rgb)/0.12)] {class_name}",
        aria_hidden="true",
    )


def _tone_text(tone: str) -> str:
    return {
        "neutral": "text-[rgb(var(--ap-paper-muted-rgb))]",
        "paper": "text-[rgb(var(--ap-paper-rgb))]",
        "accent": "text-[rgb(var(--ap-accent-rgb))]",
        "flame": "text-[rgb(var(--ap-flame-soft-rgb))]",
        "sage": "text-[rgb(var(--ap-sage-rgb))]",
        "info": "text-[rgb(var(--ap-info-rgb))]",
    }.get(tone, "text-[rgb(var(--ap-paper-muted-rgb))]")


def _tone_border(tone: str) -> str:
    return {
        "neutral": "border-[rgb(var(--ap-paper-rgb)/0.24)]",
        "paper": "border-[rgb(var(--ap-paper-rgb)/0.30)]",
        "accent": "border-[rgb(var(--ap-accent-rgb)/0.40)]",
        "flame": "border-[rgb(var(--ap-flame-rgb)/0.40)]",
        "sage": "border-[rgb(var(--ap-sage-rgb)/0.40)]",
        "info": "border-[rgb(var(--ap-info-rgb)/0.35)]",
    }.get(tone, "border-[rgb(var(--ap-paper-rgb)/0.24)]")


def tag(
    label: rx.Var | str,
    *,
    tone: str = "neutral",
    icon: str = "",
) -> rx.Component:
    """Étiquette carrée, mono, filet d'un pixel."""
    children: list[rx.Component] = []
    if icon:
        children.append(rx.icon(icon, class_name="h-3 w-3 shrink-0"))
    children.append(rx.el.span(label))
    return rx.el.span(
        *children,
        class_name=(
            "ap-mono inline-flex w-fit items-center gap-1.5 border px-2 py-1 "
            "text-[9px] uppercase tracking-[0.18em] whitespace-nowrap "
            f"{_tone_border(tone)} {_tone_text(tone)}"
        ),
    )


def action_button(
    label: rx.Var | str,
    *,
    icon: str = "",
    on_click=None,
    href: str = "",
    tone: str = "solid",
    type: str = "button",
    disabled=None,
    class_name: str = "",
) -> rx.Component:
    """Bouton carré éditorial : plein chlorophylle ou filet simple."""
    styles = {
        "solid": (
            "border border-[rgb(var(--ap-accent-rgb))] bg-[rgb(var(--ap-accent-rgb))] text-[rgb(var(--ap-ink-rgb))] "
            "hover:bg-[rgb(var(--ap-accent-soft-rgb))] hover:border-[rgb(var(--ap-accent-soft-rgb))]"
        ),
        "outline": (
            "border border-[rgb(var(--ap-paper-rgb)/0.30)] bg-transparent text-[rgb(var(--ap-paper-rgb))] "
            "hover:border-[rgb(var(--ap-accent-rgb))] hover:text-[rgb(var(--ap-accent-rgb))]"
        ),
        "ghost": (
            "border border-transparent bg-transparent text-[rgb(var(--ap-paper-muted-rgb))] "
            "hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-paper-rgb)/0.24)]"
        ),
        "flame": (
            "border border-[rgb(var(--ap-flame-rgb)/0.45)] bg-[rgb(var(--ap-flame-rgb)/0.10)] text-[rgb(var(--ap-flame-soft-rgb))] "
            "hover:bg-[rgb(var(--ap-flame-rgb)/0.20)]"
        ),
    }
    children: list[rx.Component] = []
    if icon:
        children.append(rx.icon(icon, class_name="h-3.5 w-3.5 shrink-0"))
    children.append(rx.el.span(label))
    shared = (
        "ap-press ap-mono inline-flex w-fit items-center justify-center "
        "gap-2 px-3.5 py-2.5 "
        f"text-[10px] uppercase tracking-[0.18em] transition-colors {styles[tone]} "
        "disabled:cursor-not-allowed disabled:opacity-45 "
        f"{class_name}"
    )
    if href:
        return rx.el.a(*children, href=href, class_name=shared)
    return rx.el.button(
        *children,
        type=type,
        on_click=on_click,
        disabled=disabled,
        class_name=shared,
    )


def icon_action(
    icon: str,
    label: rx.Var | str,
    *,
    on_click=None,
    href: str = "",
    class_name: str = "",
) -> rx.Component:
    shared = (
        "ap-mono inline-flex h-9 w-9 shrink-0 items-center justify-center border "
        "border-[rgb(var(--ap-paper-rgb)/0.24)] text-[rgb(var(--ap-paper-muted-rgb))] transition-colors "
        "hover:border-[rgb(var(--ap-accent-rgb))] hover:text-[rgb(var(--ap-accent-rgb))] "
        f"{class_name}"
    )
    if href:
        return rx.el.a(
            rx.icon(icon, class_name="h-4 w-4"),
            href=href,
            title=label,
            aria_label=label,
            class_name=shared,
        )
    return rx.el.button(
        rx.icon(icon, class_name="h-4 w-4"),
        type="button",
        on_click=on_click,
        title=label,
        aria_label=label,
        class_name=shared,
    )


def section_header(
    index: rx.Var | str,
    title: rx.Var | str,
    *,
    description: rx.Var | str = "",
    trailing: rx.Component | None = None,
    class_name: str = "",
) -> rx.Component:
    """Titre de section numéroté, filet supérieur, composition éditoriale."""
    children: list[rx.Component] = [
        rx.el.span(
            index,
            class_name="ap-mono text-[10px] tracking-[0.2em] text-[rgb(var(--ap-accent-rgb))]",
        ),
        rx.el.h2(
            title,
            class_name="ap-serif mt-2 text-2xl md:text-3xl text-[rgb(var(--ap-paper-rgb))]",
        ),
    ]
    if not isinstance(description, str) or description:
        children.append(
            rx.el.p(
                description,
                class_name="mt-2 max-w-2xl text-[13px] leading-relaxed text-[rgb(var(--ap-paper-muted-rgb)/0.90)]",
            )
        )
    right = trailing if trailing is not None else rx.fragment()
    return rx.el.div(
        rx.el.div(
            rx.el.div(*children, class_name="min-w-0"),
            right,
            class_name="flex flex-wrap items-end justify-between gap-4",
        ),
        class_name=f"border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-5 {class_name}",
    )


def stat(
    label: rx.Var | str,
    value: rx.Var | str,
    unit: rx.Var | str = "",
    caption: rx.Var | str = "",
    *,
    index: rx.Var | str = "",
    tone: str = "paper",
    icon: rx.Var | str | None = None,
) -> rx.Component:
    """Chiffre éditorial : filet supérieur, valeur en serif, légende mono."""
    value_children: list[rx.Component] = [
        rx.el.span(
            value,
            class_name=(
                "ap-serif block whitespace-nowrap text-[2.35rem] leading-[0.85] "
                f"{_tone_text(tone)}"
            ),
        )
    ]
    if not (isinstance(unit, str) and not unit):
        value_children.append(
            rx.el.span(
                unit,
                class_name=(
                    "ap-mono text-[10px] uppercase tracking-[0.16em] "
                    "text-[rgb(var(--ap-paper-muted-rgb)/0.78)]"
                ),
            )
        )
    value_row = rx.el.div(*value_children, class_name="mt-4 flex items-end gap-2")
    marks: list[rx.Component] = []
    if icon is not None:
        marks.append(
            rx.icon(icon, class_name="h-3.5 w-3.5 shrink-0 text-[rgb(var(--ap-paper-muted-rgb)/0.82)]")
        )
    if not (isinstance(index, str) and not index):
        marks.append(
            rx.el.span(
                index,
                class_name="ap-mono text-[9px] tracking-[0.2em] text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
            )
        )
    children: list[rx.Component] = [
        rx.el.div(
            rx.el.div(
                rx.el.span(label, class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.78)]"),
                rx.el.div(*marks, class_name="flex shrink-0 items-start gap-2"),
                class_name="flex items-start justify-between gap-3",
            ),
            value_row,
        )
    ]
    if not isinstance(caption, str) or caption:
        children.append(
            rx.el.p(
                caption,
                class_name="mt-3 text-[11px] leading-relaxed text-[rgb(var(--ap-paper-muted-rgb)/0.78)]",
            )
        )
    return rx.el.div(
        *children,
        class_name="group border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-4 pb-1",
    )


def meta_row(
    label: rx.Var | str,
    value: rx.Var | str,
    *,
    tone: str = "paper",
) -> rx.Component:
    """Ligne de registre : intitulé mono discret, valeur alignée à droite."""
    value_class = {
        "paper": "text-[rgb(var(--ap-paper-rgb))]",
        "flame": "text-[rgb(var(--ap-flame-soft-rgb))]",
        "accent": "text-[rgb(var(--ap-accent-rgb))]",
        "muted": "text-[rgb(var(--ap-paper-muted-rgb))]",
    }.get(tone, "text-[rgb(var(--ap-paper-rgb))]")
    return rx.el.div(
        rx.el.span(
            label,
            class_name=(
                "ap-mono text-[9px] uppercase tracking-[0.22em] text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"
            ),
        ),
        rx.el.span(
            value,
            class_name=(
                "ap-mono text-right text-[10px] uppercase leading-relaxed "
                "tracking-[0.14em] " + value_class
            ),
        ),
        class_name="flex items-center justify-between gap-6 py-2",
    )


def meta_ledger(*rows: rx.Component, class_name: str = "") -> rx.Component:
    """Registre de métadonnées, filets haut et bas, sans encadré."""
    return rx.el.div(
        *rows,
        class_name=(
            "divide-y divide-[rgb(var(--ap-paper-rgb)/0.10)] border-y border-[rgb(var(--ap-paper-rgb)/0.18)] "
            f"{class_name}"
        ),
    )


def page_hero(
    eyebrow_text: rx.Var | str,
    title: rx.Component | rx.Var | str,
    lede: rx.Var | str,
    *,
    tone: str = "accent",
    meta: rx.Component | None = None,
    actions: rx.Component | None = None,
    class_name: str = "",
) -> rx.Component:
    """En-tête de page unique : sur-titre, titre serif, chapô, registre, actions."""
    has_right = meta is not None or actions is not None
    right_children: list[rx.Component] = []
    if meta is not None:
        right_children.append(meta)
    if actions is not None:
        right_children.append(actions)
    right = (
        rx.el.div(
            *right_children,
            class_name=(
                "flex w-full flex-col gap-5 lg:max-w-sm lg:shrink-0 lg:self-end"
            ),
        )
        if has_right
        else rx.fragment()
    )
    return rx.el.header(
        rx.el.div(
            eyebrow(eyebrow_text, tone=tone),
            rx.el.h1(
                title,
                class_name=(
                    "ap-display mt-5 text-[clamp(2.3rem,4.2vw,3.8rem)] text-[rgb(var(--ap-paper-rgb))]"
                ),
            ),
            rx.el.p(
                lede,
                class_name=(
                    "mt-5 max-w-2xl text-[13px] leading-relaxed text-[rgb(var(--ap-paper-muted-rgb)/0.90)]"
                ),
            ),
            class_name="min-w-0 max-w-3xl",
        ),
        right,
        class_name=(
            "ap-reveal flex flex-col gap-8 lg:flex-row lg:items-end "
            f"lg:justify-between lg:gap-16 {class_name}"
        ),
    )


def index_tab(
    label: rx.Var | str,
    *,
    active,
    on_click=None,
    icon: rx.Var | str | None = None,
    class_name: str = "",
) -> rx.Component:
    """Onglet éditorial : index mono souligné, sans pastille pleine."""
    children: list[rx.Component] = []
    if icon is not None:
        children.append(
            rx.icon(
                icon,
                class_name=rx.cond(
                    active,
                    "h-3.5 w-3.5 shrink-0 text-[rgb(var(--ap-accent-rgb))]",
                    "h-3.5 w-3.5 shrink-0 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
            )
        )
    children.append(rx.el.span(label))
    return rx.el.button(
        *children,
        type="button",
        on_click=on_click,
        aria_pressed=active,
        class_name=rx.cond(
            active,
            "ap-press ap-mono inline-flex items-center gap-2 border-b border-[rgb(var(--ap-accent-rgb))] pb-2 "
            "pt-1 text-[10px] uppercase tracking-[0.18em] text-[rgb(var(--ap-accent-rgb))] "
            "transition-colors " + class_name,
            "ap-press ap-mono inline-flex items-center gap-2 border-b border-transparent pb-2 "
            "pt-1 text-[10px] uppercase tracking-[0.18em] text-[rgb(var(--ap-paper-muted-rgb)/0.78)] "
            "transition-colors hover:border-[rgb(var(--ap-paper-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] "
            + class_name,
        ),
    )


def index_rail(
    *children: rx.Component,
    label: str = "",
    class_name: str = "",
) -> rx.Component:
    """Bandeau d'onglets éditorial, filet supérieur, retrait régulier."""
    return rx.el.nav(
        *children,
        aria_label=label,
        class_name=(
            "flex w-full flex-wrap items-center gap-x-7 gap-y-2 border-t "
            f"border-[rgb(var(--ap-paper-rgb)/0.18)] pt-3 {class_name}"
        ),
    )


def refresh_button(
    *,
    on_click=None,
    loading=None,
    label: str = "Actualiser",
    class_name: str = "",
) -> rx.Component:
    """Action principale de rafraîchissement, icône animée pendant le chargement."""
    return rx.el.button(
        rx.cond(
            loading,
            rx.icon("loader-circle", class_name="h-3.5 w-3.5 animate-spin"),
            rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
        ),
        rx.el.span(label),
        type="button",
        on_click=on_click,
        disabled=loading,
        class_name=(
            "ap-press ap-mono inline-flex w-fit items-center justify-center "
            "gap-2 border border-[rgb(var(--ap-accent-rgb))] bg-[rgb(var(--ap-accent-rgb))] px-3.5 py-2.5 text-[10px] uppercase "
            "tracking-[0.18em] text-[rgb(var(--ap-ink-rgb))] transition-colors "
            "hover:border-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-soft-rgb))] "
            "disabled:cursor-not-allowed disabled:opacity-45 "
            f"{class_name}"
        ),
    )


def field(
    control: rx.Component,
    *,
    icon: str = "",
    suffix: rx.Component | None = None,
    class_name: str = "",
) -> rx.Component:
    """Champ de saisie à filet unique, sans halo, icône à gauche."""
    children: list[rx.Component] = []
    if icon:
        children.append(
            rx.icon(
                icon,
                class_name=(
                    "pointer-events-none absolute left-3 top-1/2 h-4 w-4 "
                    "-translate-y-1/2 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"
                ),
            )
        )
    children.append(control)
    if suffix is not None:
        children.append(suffix)
    return rx.el.div(*children, class_name=f"relative w-full min-w-0 {class_name}")


def input_class(*, icon: bool = False, extra: str = "") -> str:
    """Classes du champ de saisie éditorial (filet unique, sans halo)."""
    pad = "pl-9" if icon else "pl-3"
    return (
        "w-full border border-[rgb(var(--ap-paper-rgb)/0.21)] bg-[rgb(var(--ap-surface-faint-rgb))] py-2.5 pr-3 "
        f"{pad} text-sm text-[rgb(var(--ap-paper-rgb))] outline-hidden transition-colors "
        "placeholder:text-[rgb(var(--ap-paper-muted-rgb)/0.82)] focus:border-[rgb(var(--ap-accent-rgb))] "
        f"{extra}"
    )


def select_field(
    *children: rx.Component,
    name: str,
    icon: str = "list-filter",
    default_value=None,
    on_change=None,
    form_key=None,
    width: str = "w-full sm:w-64",
) -> rx.Component:
    """Sélecteur à filet unique, icône à gauche, chevron discret."""
    kwargs = {"name": name}
    if default_value is not None:
        kwargs["default_value"] = default_value
    if on_change is not None:
        kwargs["on_change"] = on_change
    if form_key is not None:
        kwargs["key"] = f"{name}-{form_key}"
    return rx.el.div(
        rx.icon(
            icon,
            class_name=(
                "pointer-events-none absolute left-3 top-1/2 h-4 w-4 "
                "-translate-y-1/2 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"
            ),
        ),
        rx.el.select(
            *children,
            class_name=input_class(
                icon=True, extra="cursor-pointer appearance-none pr-9"
            ),
            **kwargs,
        ),
        rx.icon(
            "chevron-down",
            class_name=(
                "pointer-events-none absolute right-3 top-1/2 h-4 w-4 "
                "-translate-y-1/2 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"
            ),
        ),
        class_name=f"relative {width}",
    )


def skeleton(class_name: str = "h-4 w-full") -> rx.Component:
    """Ligne de chargement : balayage d'encre, jamais un bloc gris."""
    return rx.el.div(
        class_name=f"ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] {class_name}",
        aria_hidden="true",
    )


def skeleton_rows(count: int = 4, *, avatar: bool = True) -> rx.Component:
    """Silhouette d'une liste : médaillon puis deux lignes de texte."""
    return rx.el.div(
        *[
            rx.el.div(
                skeleton("h-10 w-10 shrink-0") if avatar else rx.fragment(),
                rx.el.div(
                    skeleton("h-3 w-40"),
                    skeleton("h-3 w-24"),
                    class_name="flex flex-col gap-2",
                ),
                class_name="flex items-center gap-3 border-b border-[rgb(var(--ap-paper-rgb)/0.12)] py-4",
            )
            for _ in range(count)
        ],
        class_name="flex flex-col w-full",
        aria_busy="true",
    )


def skeleton_page(sections: int = 2, *, rows: int = 3) -> rx.Component:
    """Silhouette d'écran : surtitre, titre, chapô puis sections en lignes."""
    return rx.el.div(
        skeleton("h-2.5 w-24"),
        skeleton("mt-4 h-9 w-2/3 max-w-xl"),
        skeleton("mt-4 h-3 w-full max-w-2xl"),
        skeleton("mt-2 h-3 w-4/5 max-w-xl"),
        *[
            rx.el.div(
                skeleton("h-2.5 w-32"),
                rx.el.div(
                    *[skeleton("h-12 w-full") for _ in range(rows)],
                    class_name="mt-4 flex flex-col gap-3",
                ),
                class_name="mt-8 w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-5",
            )
            for _ in range(sections)
        ],
        class_name="flex flex-col w-full",
        aria_busy="true",
    )


def empty_state(
    icon: str,
    title: rx.Var | str,
    description: rx.Var | str = "",
    *,
    action: rx.Component | None = None,
    class_name: str = "",
) -> rx.Component:
    """État vide éditorial : filet supérieur, icône discrète, titre serif."""
    children: list[rx.Component] = [
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"),
            class_name=(
                "flex h-11 w-11 items-center justify-center border "
                "border-[rgb(var(--ap-paper-rgb)/0.18)]"
            ),
        ),
        rx.el.h3(
            title,
            class_name="ap-serif mt-5 text-xl text-[rgb(var(--ap-paper-rgb))]",
        ),
    ]
    if not isinstance(description, str) or description:
        children.append(
            rx.el.p(
                description,
                class_name=(
                    "mt-2 max-w-md text-[12px] leading-relaxed text-[rgb(var(--ap-paper-muted-rgb)/0.82)]"
                ),
            )
        )
    if action is not None:
        children.append(rx.el.div(action, class_name="mt-5"))
    return rx.el.div(
        *children,
        class_name=(
            f"ap-sheet flex w-full flex-col items-start border-t border-[rgb(var(--ap-paper-rgb)/0.18)] "
            f"pt-8 pb-2 {class_name}"
        ),
    )
