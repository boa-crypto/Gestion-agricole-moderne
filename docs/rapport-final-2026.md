# Rapport final — refonte AgriPro, automne 2026

Branche `arena/00bd4dc1-gestion-agricole-moderne`, dépôt
`boa-crypto/Gestion-agricole-moderne`. Point de départ : `2df4464`
(`main`). État livré : `78c0610`. Ce rapport suit les onze points demandés
dans l'ordre.

---

## 1. État initial

Reflex 0.10, `reflex-enterprise`, interface entièrement en français,
16 routes protégées par `guarded_page`, sous-states métier abondants
(CRM, parcelles, stocks, RH, matériel, charges, guide, administration,
audit).

Défauts relevés en phase 1 (détail complet : `docs/audit-refonte-2026.md`) :

- aucune couche de design partagée : quatre-vingt-quinze fichiers de composants
  définissaient chacun leurs encadrés, leurs tailles de texte et leurs couleurs ;
- ~110 panneaux « boîte dans la boîte » (`border` + `background` + `padding`) ;
- 67 blocs de chargement gris (`animate-pulse`) sans rapport avec le contenu
  attendu ;
- états vides hétérogènes, souvent un simple paragraphe centré ;
- aucune animation, aucun anneau de focus global, aucune règle
  `prefers-reduced-motion` ;
- montants financiers affichés sans séparateurs de milliers ;
- suite de tests partiellement inopérante.

## 2. Méthode MCP Figma

Procédure officielle consultée le 31 octobre 2026
(`developers.figma.com/docs/figma-mcp-server`), consignée dans
`docs/figma-mcp.md` : serveur distant `https://mcp.figma.com/mcp` avec OAuth
(recommandé), ou serveur local piloté par l'application de bureau. Installation
côté Claude Code par plugin (`claude plugin install figma@claude-plugins-official`)
ou par ajout manuel (`claude mcp add --scope user --transport http figma
https://mcp.figma.com/mcp`), puis `/mcp` → Authenticate.

## 3. Résultat des tests de connexion

**Le MCP n'a pas pu être installé depuis cet espace de travail, et ce n'est pas
simulé.** Trois blocages mesurés :

| Vérification | Résultat |
| --- | --- |
| `command -v claude` | absent |
| `curl https://mcp.figma.com/mcp` | `000` (sortie réseau filtrée) |
| `curl https://api.figma.com/v1/me` | `000` |
| Configuration MCP existante | aucune |

L'authentification Figma exige un navigateur et un compte personnel : elle ne
peut pas être déléguée à un agent distant. Aucun serveur MCP n'est donc déclaré,
aucun appel d'outil n'a été tenté.

## 4. Outils accessibles

Relevé documentaire (pas d'appel réel possible) dans `docs/figma-mcp.md` §6 :

- **Lecture** : `get_design_context`, `get_metadata`, `get_screenshot`,
  `get_variable_defs`, `get_motion_context`, `get_figjam`,
  `get_code_connect_map`, `get_code_connect_suggestions`, `get_libraries`,
  `search_design_system`, `whoami` ;
- **Écriture / création** : `add_code_connect_map`, `create_design_system_rules`,
  `create_new_file`, `create_generative_plugin`, `create_shader`,
  `generate_diagram` (certains réservés au siège Full) ;
- **Ressources** : `download_assets`, extraction de contexte vers le code,
  export de frames vers le code.

## 5. Direction artistique

« Encre & Chlorophylle » : une maison d'édition agricole, pas un tableau de
bord SaaS générique. Pas de verre dépoli, pas de dégradé décoratif, aucun coin
arrondi.

- **Palette** : encre `#0A0A08` / `#060604`, surfaces `#101208` `#14160F`
  `#191C13` `#20241A`, papier `#F2EFE4` / `#C9C5B4` / `#8F8C7E`, chlorophylle
  `#D8FA5E` / `#B6D93F`, vermillon `#FF5A2B`, sauge `#A9C98B`, info `#9CC3FF`,
  danger `#FF6B5A`.
- **Typographie** : Instrument Serif (titres), Inter Tight (texte),
  JetBrains Mono (surtitres et chiffres).
- **Filets** : `/12`, `/8`, `/22` ; rayons zéro ; grain de papier en
  surimpression.
- **Jetons** : `docs/design-tokens.json` au format Tokens Studio, prêt à être
  importé dans Figma ; `docs/editorial-design.md` décrit les règles écran par
  écran.

## 6. Écrans redesignés

Coque commune (`shell`, `side_rail`, `cockpit_header`, `kpi_strip`) plus les
seize routes :

| Route | Traitement |
| --- | --- |
| `/` | cockpit éditorial, bandeau de chiffres, héros, index de modules |
| `/configuration` | sections en filets, champs unifiés |
| `/parcelles` | double page liste / fiche, état vide de cultures |
| `/referentiel` | arbre de cultures, cartes en filets |
| `/phenologie` | panneaux et administration phénologique |
| `/traitements` | journal d'interventions, lignes compactes |
| `/employes` | liste + fiche, silhouettes de chargement |
| `/maintenance` | engins, atelier, journal |
| `/cartographie` | double page îlots / carte, dessin assisté, contrôle des contours |
| `/rapports` | synthèse phénologique |
| `/charges` | registre financier, filets, état vide partagé |
| `/crm` | 14 onglets, registres, montants formatés, espace tiers |
| `/recherche` | résultats groupés |
| `/guide` | bibliothèque embarquée, sept sections |
| `/administration` | quinze panneaux, organigramme, fiche utilisateur |
| `/audit` | matrice, diagnostic, sécurité |

## 7. Animations et micro-interactions

- `ap-reveal` (620 ms) sur les héros, `ap-stagger` (55 ms) sur les grilles,
  `ap-press` au clic, `ap-panel` et `ap-row` sur les panneaux et les listes ;
- `ap-skeleton` (balayage 1,7 s), `ap-overlay` (180 ms), `ap-sheet` (260 ms),
  `ap-toast` (220 ms) ;
- affordance globale des boutons : transition 140 ms, enfoncement d'un pixel,
  opacité réduite et curseur explicite à l'état désactivé ;
- anneau de focus `:focus-visible` chlorophylle sur tous les éléments
  interactifs, navigation clavier des onglets et des sélecteurs ;
- `prefers-reduced-motion: reduce` neutralise l'ensemble des animations et des
  défilements.

## 8. Fichiers

177 fichiers modifiés (9 772 insertions, 6 977 suppressions) depuis `2df4464` :
101 composants, 16 pages, 10 états, 5 tests, 14 aperçus versionnés, 6 documents.

Documents de référence :

- `docs/audit-refonte-2026.md` — audit initial et état des défauts ;
- `docs/editorial-design.md` — direction artistique, lots 1 à 8 ;
- `docs/design-tokens.json` — jetons importables ;
- `docs/figma-mcp.md` — diagnostic et procédure MCP ;
- `docs/validation-routes-2026.md` — parcours des routes et erreurs console ;
- `scripts/preflight.py` — construction de tous les écrans ;
- `scripts/tools/route_tour.js` — parcours automatisé des routes.

## 9. Tests et build

| Contrôle | Commande | Résultat |
| --- | --- | --- |
| Compilation | `python scripts/preflight.py --compile` | `compileall : OK` |
| Construction des écrans | `python scripts/preflight.py` | 16/16, « Tous les écrans se construisent. » |
| Tests exécutables | `python -m pytest` sur les 20 modules collectables | **124 réussis, 1 échec réseau** (`test_weather`, sortie internet coupée) |
| Scripts hérités | `python scripts/run_legacy_tests.py` | **19 scripts sur 26** (détail : `docs/validation-scripts-2026.md`) |
| Parcours des routes | `node scripts/tools/route_tour.js` | 16 routes sur 16 en 200, aucune erreur applicative en console |

Quatre tests périmés ont été réparés (comparaisons de copie, attributs
supprimés par la refonte, appel non attendu d'une méthode asynchrone, référence
orpheline rejetée par la clé étrangère) — détail dans
`docs/editorial-design.md` §10.

## 10. Problèmes restants

1. **MCP Figma non installé** : blocage réseau et absence de Claude Code, décrit
   au point 3. La procédure exacte est prête à être exécutée côté poste Windows.
2. **Sept scripts hérités échouent encore** : cinq exigent une session métier
   vérifiée (le garde les refuse, à raison), deux réclament un contexte
   d'événement Reflex, quatre portent sur des jeux de démonstration incomplets
   ou sur des assertions antérieures à la refonte. Détail et causes :
   `docs/validation-scripts-2026.md`.
3. **Chargement au montage** : les panneaux CRM sont corrigés — le chargement
   est déclenché côté serveur, après `verify_page`, par
   `NavigationState.load_crm_panel` ; vérifié à l'écran sur `?vue=ventes`
   (3 pièces) et `?vue=clients` (3 tiers). La liste des parcelles et la page
   phénologie attendent le même traitement.
4. **Données de démonstration incomplètes** : les seeders ne couvrent ni le
   guide, ni les charges, ni l'administration, ni l'audit — ces écrans
   s'affichent avec leurs états vides.
5. **Contrastes** : les légendes en `#C9C5B4/45` restent autour de 3:1 sur
   l'encre ; à relever si l'accessibilité stricte devient exigée.

## 11. Lancement

```powershell
# 1. Environnement
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Dépendances front (une fois)
$env:REFLEX_USE_NPM = "1"

# 3. Contrôles avant démarrage
python scripts/preflight.py --compile
python -m pytest tests/test_crm.py tests/test_navigation.py tests/test_local_login.py -q

# 4. Application
reflex run
```

L'application écoute sur <http://localhost:3000> (interface) et
<http://localhost:8000> (backend). Un `.env` local doit fournir la base et, le
cas échéant, le jeton `reflex-enterprise` — aucun de ces secrets n'est versionné.

```powershell
# Parcours automatisé des routes (facultatif)
node scripts/tools/route_tour.js http://localhost:3000 rapport.json 4000
```
