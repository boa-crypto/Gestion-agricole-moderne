# Direction artistique — « Encre & Chlorophylle »

Refonte graphique complète d'AgriPro : la grammaire du tableau de bord sombre
et vitré cède la place à une **maquette de maison d'édition agronomique**.
L'application se lit désormais comme un ouvrage : masthead, sommaire numéroté,
titres en serif éditoriale, filets d'un pixel, chiffres alignés et un seul
accent chlorophylle.

## 1. Principes

1. **Le papier avant le verre.** Plus de flous, plus de coins arrondis, plus de
   cartes translucides : des surfaces d'encre pleines, des angles vifs et des
   filets de 1 px structurent la page.
2. **La typographie porte la hiérarchie.** Trois familles seulement :
   `Instrument Serif` pour les titres et les chiffres, `Inter Tight` pour la
   lecture, `JetBrains Mono` pour les sur-titres, les libellés et les données.
3. **Un accent, pas dix.** Le vert chlorophylle acide signale l'interaction et
   l'état actif. Le vermillon signale l'attention. Tout le reste est encre et
   papier.
4. **La grille est visible.** Chaque bloc est séparé par un filet supérieur, les
   sections sont numérotées (`01`, `02`, …), les colonnes respirent.
5. **Aucune fausse fonctionnalité.** La refonte est strictement visuelle : les
   routes, les droits, les états Reflex et les validations serveur sont
   inchangés.

## 2. Jetons

| Jeton | Valeur | Usage |
| --- | --- | --- |
| `INK` | `#0A0A08` | fond de page |
| `INK_DEEP` | `#060604` | voiles de dialogue |
| `SURFACE` | `#101208` | panneaux |
| `SURFACE_RAISED` | `#14160F` | cartes |
| `SURFACE_HIGH` | `#191C13` | survol, champs |
| `PAPER` | `#F2EFE4` | texte principal |
| `PAPER_MUTED` | `#C9C5B4` | texte secondaire |
| `ACCENT` | `#D8FA5E` | chlorophylle, interaction |
| `FLAME` | `#FF5A2B` | alerte, signal |
| `SAGE` | `#A9C98B` | succès, croissance |
| `INFO` | `#9CC3FF` | information |
| `DANGER` | `#FF6B5A` | erreur |

Typographies (Google Fonts) : `Instrument Serif` (400, italique), `Inter Tight`
(300–700), `JetBrains Mono` (300–600).

Les jetons sont centralisés dans `app/components/design.py` (constantes Python
et variables CSS `--ap-*`).

## 3. Composants de la coque

- `app/components/shell.py` — `app_shell(content, active)` : masthead fixe
  (marque, fil d'Ariane mono, sélecteur de cockpit, recherche, aide, session),
  index latéral numéroté, bandeau de domaines dépliable, colophon.
- `app/components/side_rail.py` — index vertical numéroté (`01` → `17`) et
  tiroir mobile.
- `app/components/design.py` — variables CSS globales, grain d'impression,
  primitives (`eyebrow`, `hairline`, `tag`, `action_button`, `icon_action`,
  `section_header`, `stat`).
- `app/components/cockpit_header.py` / `kpi_strip.py` — hero éditorial et
  bandeau de chiffres clés.
- `app/components/menu_auth.py` — planche de couverture de connexion et états de
  session, sans carte flottante.

## 4. Migration et maintenance

Deux scripts documentent la bascule et restent réutilisables :

```bash
python tools/editorial_remap.py --dry-run    # palette, surfaces, rayons, flous
python tools/editorial_headers.py --dry-run  # héros de page, micro-libellés
python tools/page_shell_migration.py --dry-run  # coque commune des pages
```

Règles de style à respecter pour toute nouvelle vue :

- `ap-mono` pour tout libellé court, `ap-serif`/`ap-display` pour les titres.
- Aucun rayon d'arrondi ; filet `border-[#F2EFE4]/12` ; surface
  `bg-[#101208]` ou `bg-[#14160F]`.
- Accent `text-[#D8FA5E]` réservé à l'état actif et aux actions principales ;
  vermillon `text-[#FF8A5B]` pour les alertes.
- Les libellés décoratifs conservent un contraste ≥ 3:1 ; le texte de lecture
  reste en `text-[#F2EFE4]` ou `text-[#C9C5B4]/70`.

## 5. Accessibilité et mouvement

- Anneau de focus global `1px solid var(--ap-accent)` avec décalage de 3 px.
- `aria_*` d'origine conservés (fils d'Ariane, `aria-current`, `aria-pressed`,
  libellés des boutons icônes).
- Grain, animations et transitions neutralisés via
  `prefers-reduced-motion: reduce`.
- Contraste : papier `#F2EFE4` sur encre `#0A0A08` (≈ 17:1), libellés atténués
  ≥ 3:1, aucun texte porté par le seul accent sur fond clair.
