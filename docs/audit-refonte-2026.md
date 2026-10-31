# Audit de la refonte AgriPro — état au 31 octobre 2026

Document de travail pour la mission « redesign premium ». Il fige l'état réel du
dépôt avant toute nouvelle transformation, et sert de référence aux lots
suivants.

## 1. Socle technique

| Élément | Valeur constatée |
| --- | --- |
| Framework | Reflex 0.10.0 (Python → React 19 + react-router 8), thème Radix 3 |
| Langages | Python 3.11 (application), CSS (feuille globale injectée), TypeScript généré |
| Extension métier | `reflex-enterprise` 0.9.10 (menus, rôles, permissions, journal) |
| Base | SQLite en développement, PostgreSQL en production (`psycopg`) |
| Dépendances directes | `reflex[db]`, `aiosqlite`, `reflex-enterprise`, `requests`, `pillow`, `psycopg` |
| Frontend | Vite / react-router dev (`REFLEX_USE_NPM=1`, pas de bun dans l'environnement) |
| Ports | 3000 (front dev), 8000 (backend réflexe) |

Aucun build statique n'est versionné : l'application se sert en mode `reflex run`.

## 2. Architecture

```
app/
  app.py              # 16 routes, toutes protégées par guarded_page()
  components/         # 102 composants (coque, primitives, panneaux métier)
  pages/              # 17 écrans
  states/             # 31 états Reflex
  *_reference.py      # référentiels métier (cultures, audit, accès, catalogue)
  *_rules.py          # règles métier pures (CRM, géométrie, exports)
tests/                # 45 fichiers unittest
docs/                 # direction artistique, aperçus, ce document
```

Séparation stricte : les composants ne calculent aucune règle métier, les états
exposent des variables dérivées `*_display`, les modules `*_rules.py` restent
testables sans Reflex.

## 3. Routes et protection

| Route | Écran | Garde |
| --- | --- | --- |
| `/` | cockpit agronomique | `guarded_page(…, "/")` |
| `/configuration` | menus, rôles, comptes | garde + droit administrateur |
| `/parcelles` | parcelles & cultures | garde |
| `/referentiel` | catalogue cultures | garde |
| `/phenologie` | stades culturaux | garde |
| `/traitements` | interventions, récoltes | garde |
| `/employes` | registre RH | garde |
| `/maintenance` | engins & atelier | garde |
| `/cartographie` | carte et contours | garde |
| `/rapports` | état phénologique | garde |
| `/charges` | registre financier | garde |
| `/crm` | 14 vues commerciales | garde |
| `/recherche` | console transversale | garde |
| `/guide` | guide documentaire | garde |
| `/administration` | 11 sections | garde + droit administrateur |
| `/audit` | audit fonctionnel | garde |

Aucune route n'est publique : `guarded_page` vérifie le jeton, le rôle et la
politique de menu avant de rendre le contenu.

## 4. Ce qui a déjà été transformé

Trois lots ont été livrés (`b8b7edd`, `6c19339`, `4da760d`) :

1. **Coque éditoriale** — masthead, rail latéral, pied de page, palette
   « Encre & Chlorophylle », typographies éditoriales, grain d'impression.
2. **Primitives de héros** — `page_hero`, `meta_row`/`meta_ledger`, `stat`,
   `index_tab`/`index_rail`, `action_button`, `icon_action`.
3. **Registres** — héros et chiffres unifiés sur employés, charges,
   maintenance, traitements, administration, cartographie, rapports,
   recherche, audit ; champs et sélecteurs unifiés (`field`, `input_class`,
   `select_field`) ; `index_tab` pour les sections d'administration.

## 5. Défauts encore présents

| Catégorie | Constat | Portée |
| --- | --- | --- |
| Surfaces | cartes encadrées `CARD` **résolues** (filet supérieur) ; restent les panneaux de cartographie et les tuiles interactives | ~10 composants |
| Tableaux | en-têtes non normalisés en mono, pagination hétérogène, densité variable | CRM, stocks, charges |
| Chargements | 67 `animate-pulse` bruts : squelettes gris génériques, sans lien avec la silhouette réelle | 54 fichiers |
| Mouvement | **résolu** : héros en `ap-reveal`, grilles en `ap-stagger`, clic en `ap-press`, squelettes balayés | global |
| États vides | **résolus sur 17 blocs** via `empty_state()` ; quelques messages ponctuels subsistent | ~4 écrans |
| Responsive | vérifié sur 390 px pour le cockpit et les RH ; non revérifié sur les écrans lourds (CRM, administration, cartographie) | 6 écrans |
| Accessibilité | focus visible global présent ; contrastes des légendes `text-[#C9C5B4]/45` à surveiller (≈ 3:1 sur encre) | global |
| Données de démonstration | les seeders ne couvrent ni le guide, ni les charges, ni l'administration, ni l'audit | aperçus |

## 6. Commandes de lancement, de test et de validation

```powershell
# Environnement de développement
.venv\Scripts\Activate.ps1
reflex run --env dev --frontend-port 3000 --backend-port 8000

# Vérification syntaxique et imports
python -m compileall -q app
python -c "import app.app"

# Tests (baseline connue : 68 tests, 33 erreurs liées à ReflexRuntimeError)
python -m unittest tests.test_server_guard tests.test_auth_entry `
  tests.test_menu_policy tests.test_menu_policy_admin tests.test_navigation `
  tests.test_menu_configuration tests.test_menu_session_errors
```

`pytest tests/` reste inopérant (`ModuleNotFoundError: test_utils`) : les tests
sont écrits pour `unittest`.

## 7. Protection du dépôt

- Branche de travail : `arena/00bd4dc1-gestion-agricole-moderne`, propre avant
  chaque lot.
- Aucun secret, jeton ni identifiant n'est versionné ; les variables
  d'environnement passent par `.env` local (hors dépôt).
- Chaque lot est validé par compilation, imports de toutes les pages, tests
  unittest et captures d'écran avant commit.
