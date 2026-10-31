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

## 6. Primitives partagées (lot 2)

Le second lot remplace les compositions ad hoc des en-têtes et des indicateurs
par cinq primitives de `app/components/design.py` :

| Primitive | Rôle | Écrans déjà migrés |
| --- | --- | --- |
| `page_hero` | sur-titre, titre serif, chapô, registre et actions | cockpit, CRM, guide, référentiel, parcelles |
| `meta_row` / `meta_ledger` | registre de métadonnées à filets, sans encadré | cockpit, CRM, guide, référentiel, parcelles |
| `stat` | chiffre éditorial : filet supérieur, valeur serif, unité mono, légende | chiffres clés, CRM, guide, référentiel, filtres parcellaires |
| `index_tab` / `index_rail` | index d'onglets mono souligné, sans pastille pleine | CRM (14 vues), guide (8 sections) |
| `action_button` / `icon_action` | actions carrées : plein chlorophylle, filet, fantôme | coque, en-têtes |

Règles issues des aperçus (`docs/apercus/`) :

- Un seul registre de métadonnées par page, aligné sur la colonne de droite du
  héros ; les actions se placent sous ce registre, jamais à côté du chapô.
- Un seul onglet actif par bandeau, signalé par un filet chlorophylle et un
  texte chlorophylle — pas de fond plein, pas de pastille.
- Les montants passent par des variables dérivées (`revenue_display`,
  `turnover_display`…) pour obtenir le séparateur de milliers fin (U+202F) ;
  ne jamais formater un montant à la volée dans un composant.
- Les grilles de montants utilisent trois colonnes au plus en `xl` : les
  valeurs serif longues ne tiennent pas dans six colonnes.
- Les squelettes de chargement reprennent la silhouette de la primitive
  (filet + ligne + chiffre), jamais un bloc plein.

### Chantiers restants

- Cartographie, administration, charges, RH et configuration : panneaux,
  barres d'outils et sélecteurs encore composés en cartes encadrées
  (voir `06-cartographie.jpg`).
- Menus déroulants et champs de formulaire : unifier sur le champ à filet
  unique de `parcel_filters`.
- Tables de données (CRM, stocks) : passer les en-têtes en mono et les
  montants par les variables `*_display`.

## 7. Registres et postes de travail (lot 3)

Le troisième lot étend les primitives aux pages de registre et achève
l'unification des champs. Trois primitives ont été ajoutées à
`app/components/design.py` :

| Primitive | Rôle |
| --- | --- |
| `refresh_button(on_click, loading, label)` | action principale d'actualisation : icône animée pendant le chargement, bouton désactivé |
| `field(control, icon, suffix)` | enveloppe de positionnement d'un champ (icône à gauche, suffixe à droite) |
| `input_class(icon=…, extra=…)` | classes uniques du champ de saisie : filet `#F2EFE4/14`, fond `#0F110A`, focus chlorophylle |
| `select_field(*options, name, icon, …)` | sélecteur complet : icône, chevron, `form_key` pour rejouer le DOM après chargement |

### Pages migrées

| Page | En-tête | Chiffres | Filtres |
| --- | --- | --- | --- |
| `/employes` | `page_hero` + registre (jour, absences) | `stat` ×6 + 4 compteurs | `field` + `select_field` ×3 |
| `/charges` | `page_hero` + registre (jour, reste à régler) | `stat` ×6 | `section_header`, `field`, `select_field` ×4, dates, pastilles mono |
| `/maintenance` | `page_hero` + registre (jour, opérations en retard) | `stat` ×6 + 4 compteurs | `field` + `select_field` ×3 |
| `/traitements` | `page_hero` + registre (jour, chantiers en retard) | `stat` ×6 | inchangés (lot 4) |
| `/administration` | `page_hero` + registre (jour, session) | `stat` ×6 | `field` + `select_field` ×3, `action_button` |
| `/administration` (sections) | `index_tab` remplace les boutons pleins | — | — |
| `/cartographie` | `page_hero` + registre (jour, contours) | — | panneaux intérieurs à migrer |
| `/rapports` | `page_hero` + registre (jour) | — | — |
| `/recherche` | `page_hero` + registre (jour, périmètre) | `stat` ×3 | barre soulignée, dates `field`, pastilles mono |
| `/audit` | `page_hero` + registre (relevé, constats) | `stat` ×6 | — |
| `/configuration` | `page_hero` (titre à italique chlorophylle) + registre (session, périmètre) | — | erreurs à filet vermillon |

### Règles complémentaires

- Un en-tête de page ne se compose plus à la main : `page_hero` fournit le
  sur-titre, le titre, le chapô, le registre et la colonne d'actions. Les pages
  conservent seulement une fonction locale (`_space_header`, `_header`) qui
  l'appelle, pour ne pas toucher aux points d'entrée.
- La recherche globale occupe toujours une ligne entière, au-dessus des
  sélecteurs : un champ partagé avec quatre sélecteurs tombe sous 100 px.
- Les unités de `stat` restent courtes (`h/sem`, `€/sem`, `/ 100`) ; au-delà,
  elles débordent de la colonne de 352 px.
- Les libellés de sélecteur français dépassent 200 px : largeur minimale
  `sm:w-64`, jamais `sm:w-52`.
- Un `stat` ne porte pas de texte libre long (« Tout l'historique ») : ce
  genre de valeur va dans une étiquette (`tag`) ou dans le registre du héros.
- Les états d'erreur passent au filet latéral vermillon, avec
  `action_button(..., tone="outline")` pour la relance.

### Chantiers restants

- Cartographie : barre d'îlots, outils de dessin et panneaux de navigation
  encore en cartes encadrées ; migrer vers `section_header` + `field`.
- Administration : panneaux internes (`admin_library`, `admin_org`,
  `admin_operations`, `admin_user_detail`) toujours en cartes `CARD` ;
  prévoir une variante « fiche » de `stat` et un `panel` à filet supérieur.
- Traitements, rapports et audit : barres de filtres et tableaux à aligner sur
  `select_field` et les en-têtes mono.
- Tables de données (CRM, stocks, charges) : en-têtes mono, montants via
  `*_display`, pagination en index.
- États vides : unifier les squelettes et les messages vides sur le registre
  éditorial (filet + ligne + légende).
