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
| Surfaces | **résolues** : balayage de 187 chaînes dans 66 fichiers ; un seul panneau encadré subsiste (tiroir `nav-context`, volontairement flottant) | 1 composant |
| Tableaux | en-têtes non normalisés en mono, pagination hétérogène, densité variable | CRM, stocks, charges |
| Chargements | **résolus** : `skeleton_rows` pour les listes, `skeleton_page` pour les écrans, `ap-skeleton` partout ailleurs ; une seule animation `animate-pulse` subsiste (trait d'attente de l'authentification) | 1 occurrence |
| Mouvement | **résolu** : héros en `ap-reveal`, grilles en `ap-stagger`, clic en `ap-press`, squelettes balayés | global |
| États vides | **résolus sur 17 blocs** via `empty_state()` ; quelques messages ponctuels subsistent | ~4 écrans |
| Responsive | vérifié sur 390 px pour le cockpit et les RH ; non revérifié sur les écrans lourds (CRM, administration, cartographie) | 6 écrans |
| Accessibilité | focus visible global présent ; contrastes des légendes `text-[#C9C5B4]/45` à surveiller (≈ 3:1 sur encre) | global |
| Données de démonstration | les seeders ne couvrent ni le guide, ni les charges, ni l'administration, ni l'audit | aperçus |
| Chargement initial CRM | dans l'aperçu, les onglets Ventes/Clients s'affichent vides au premier rendu : l'événement `on_mount` du panneau n'est pas exécuté, il faut cliquer « Actualiser ». Reproduit à l'écran le 31/10 ; les mêmes données apparaissent immédiatement après le clic | 2 panneaux |
| Suite de tests | `tests/test_utils.py` absent du dépôt : 25 modules non collectables | 25 fichiers |

## 6. Commandes de lancement, de test et de validation

```powershell
# Environnement de développement
.venv\Scripts\Activate.ps1
reflex run --env dev --frontend-port 3000 --backend-port 8000

# Vérification syntaxique et imports
python -m compileall -q app
python -c "import app.app"

# Tests exécutables (124 réussis, 1 échec réseau en bac à sable)
$env:PYTHONPATH = "/tmp/rxe_shim;.;tests"
python -m pytest tests/test_access.py tests/test_crm.py tests/test_crm_overview.py `
  tests/test_crm_partners.py tests/test_crm_registers.py tests/test_navigation.py `
  tests/test_local_login.py tests/test_menu_policy.py -q
```

**État réel de la suite.** `pytest` fonctionne sur vingt modules. Les
vingt-cinq autres fichiers de `tests/` sont des scripts autonomes
(`async def main()`) qui importaient un `tests/test_utils.py` jamais versionné.
Ce fichier est désormais reconstitué, et `scripts/run_legacy_tests.py` les
exécute : **18 sur 25 réussissent**, les sept autres étant documentés dans
`docs/validation-scripts-2026.md`. Le rétablissement du harnais a révélé deux
bugs applicatifs réels (appels de méthodes privées sans `self` dans
`contour_state.py` et `remediation_state.py`), corrigés depuis.

Le sous-ensemble exécutable — vingt modules — donne **124 tests réussis et un
seul échec** : `test_weather::test_build_payload_from_api`, qui sort sur le
réseau, impossible en bac à sable. La baseline `unittest` (68 tests, 33
`ReflexRuntimeError`) reste mesurable mais ne couvre que sept modules.

## 7. Protection du dépôt

- Branche de travail : `arena/00bd4dc1-gestion-agricole-moderne`, propre avant
  chaque lot.
- Aucun secret, jeton ni identifiant n'est versionné ; les variables
  d'environnement passent par `.env` local (hors dépôt).
- Chaque lot est validé par compilation, imports de toutes les pages, tests
  unittest et captures d'écran avant commit.
