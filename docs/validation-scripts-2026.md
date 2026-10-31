# Scripts de vérification hérités — état au 31 octobre 2026

Vingt-six fichiers de `tests/` ne sont pas des modules pytest : ce sont des
scripts autonomes (`async def main()`), écrits avant l'adoption de pytest. Tous
importaient `run_event` depuis `tests/test_utils.py`, **fichier jamais
versionné** : aucun ne pouvait s'exécuter.

Ce lot rétablit le harnais.

## Ce qui a été fait

1. **`tests/test_utils.py` reconstitué** — `run_event()` exécute un gestionnaire
   d'événement Reflex hors navigateur : les générateurs asynchrones sont
   consommés, les coroutines attendues, les fonctions synchrones appelées. Le
   module rétablit aussi l'instanciation directe des états (`StockState()`),
   que Reflex 0.10 refuse, pour les besoins des scripts uniquement.
2. **Syntaxe JavaScript corrigée** — 147 `.length()`, 18 `.contains()` et
   2 négations `~x` (traductions d'un code JS) remplacés par `len(...)`,
   `... in ...` et `... not in ...`.
3. **Neuf appels applicatifs fautifs corrigés**, révélés par les scripts :

   | Fichier | Défaut | Effet |
   | --- | --- | --- |
   | `app/states/contour_state.py` | `await ContourState._decide_and_report(parcel_id, …)` sans `self` (2 appels) | vérifier ou programmer le relevé d'un contour levait `AttributeError` : les deux boutons de décision étaient inopérants |
   | `app/states/remediation_state.py` | `await RemediationState._watch_alert / _decide_stock / _decide_contour(…)` sans `self` (7 appels) | mettre sous surveillance, arbitrer un stock ou trancher un contour levait `AttributeError` depuis l'interface |

   Les deux négations `~x in y` (au lieu de `x not in y`) étaient des restes
   de JavaScript : `~` y calcule le complément binaire d'un entier, l'assertion
   ne pouvait pas être vraie.

4. **Exécuteur** — `scripts/run_legacy_tests.py` lance les scripts un par un,
   restaure la base avant chacun (la suite est ainsi reproductible) et rend un
   code de sortie non nul en cas d'échec.

```powershell
python scripts/run_legacy_tests.py            # tout
python scripts/run_legacy_tests.py stock guide
```

`test_crm_panel_load` est le seul script écrit après coup : il verrouille le
chargement serveur des panneaux CRM (voir plus bas).

## Résultat : 19 scripts sur 26 réussis

| Script | État | Remarque |
| --- | --- | --- |
| `test_audit` | réussi | |
| `test_cartography` | réussi | |
| `test_catalog` | réussi | |
| `test_catalog_bridge` | réussi | |
| `test_catalog_browser` | réussi | |
| `test_contour` | réussi | après correctif `self` |
| `test_contour_api` | réussi | |
| `test_crm_panel_load` | réussi | chargement des panneaux CRM hors montage |
| `test_expenses` | réussi | |
| `test_guide_admin` | réussi | |
| `test_guide_interface` | réussi | après correctif `~` → `not in` |
| `test_help_context` | réussi | |
| `test_maintenance` | réussi | |
| `test_module_integration` | réussi | |
| `test_phenology_ops` | réussi | |
| `test_remediation` | réussi | après correctif `self` |
| `test_remediation_api` | réussi | après correctif `~` → `not in` |
| `test_search` | réussi | |
| `test_stock` | réussi | |
| `test_admin_operations` | échec | `PermissionError: Une session métier vérifiée est requise` |
| `test_delegation_expiry` | échec | idem |
| `test_phenology_admin` | échec | idem |
| `test_administration_state` | échec | `LookupError: EventContext` — `load_administration` appelle `self.get_state(MenuAuthState)`, qui exige un contexte d'événement Reflex |
| `test_security_integration` | échec | idem |
| `test_corrections` | échec | 15 sous-entités non amorcées (`expense`, `assignment`, `employee_skill`, `equipment`, `product`…) |
| `test_guide` | échec | 12 procédures en base contre 6 dans `PROCEDURES` |

## Chargement serveur des panneaux CRM

`on_mount` n'est pas rejoué lors d'une navigation cliente ni lors d'un accès
direct par URL : `/crm?cockpit=commercial&vue=ventes` affichait un registre vide
alors que la base contenait trois pièces. Le lot 10 déplace le chargement dans
la chaîne d'événements du serveur :

1. `CrmRegistersState._load()` / `CrmPartnersState._load()` portent le
   chargement complet (base, semis, requêtes, totalisation) hors de tout
   montage ; `load_registers` / `load_space` ne font plus qu'afficher puis
   appeler `_load()`.
2. `enter_register_now()` / `enter_space_now()` permettent à un autre état de
   préparer et charger un panneau (filtres remis à zéro si la cible change).
3. `NavigationState.load_crm_panel` est déclaré chargeur de page dans
   `register_loaders("crm", …)`, donc exécuté **après** `verify_page` : c'est le
   seul point où `page_allowed` est fiable. Un `yield` ne suffisait pas, la
   suite du gestionnaire s'exécutant avant la vérification.
4. Chaque panneau mémorise ce qu'il a chargé (`loaded_register`, `loaded_space`) :
   le montage ne recharge pas un panneau déjà en mémoire. Un chargement en
   cours est également signalé (`loading_register`, `loading_space`) pour
   qu'un second événement — le montage arrivant pendant la navigation — ne
   lance pas une requête concurrente qui écraserait la première.

### Les cinq échecs de sécurité

`app/server_guard.py` exige un contexte d'événement vérifié (`CHECKED_CONTEXT`)
et une politique résolue ; `load_administration` et consorts appellent
`self.get_state(MenuAuthState)`, qui n'existe qu'à l'intérieur d'un tel
contexte. Les scripts appellent les gestionnaires directement : le refus est le
comportement attendu. Les faire passer supposerait de simuler une session, une
politique et un contexte d'événement complets dans le harnais — c'est-à-dire de
désactiver le garde dans les tests. Décision assumée : laissé en l'état et
documenté, plutôt que contourné.

### Les deux échecs de contenu

- **`test_corrections`** compare la base à la liste des sous-entités attendues
  par le seeder de corrections ; quinze d'entre elles (`expense`,
  `expense_type`, `assignment`, `employee_skill`, `employee`, `skill`,
  `equipment`, `maintenance_operation`, `stock_movement`, `product`…) ne sont
  pas amorcées. C'est le manque de données de démonstration déjà signalé dans
  l'audit, pas une régression de la refonte.
- **`test_guide`** attend `len(PROCEDURES)` procédures, soit 6. Or
  `app/seed_corrections.py` en ajoute six autres (`proc-prendre-en-main-agripro`,
  `proc-suivre-stades-culture`, `proc-preparer-lit-de-semence`,
  `proc-declencher-tour-eau`, `proc-apport-azote-fractionne`,
  `proc-affecter-personne-habilitee`) : la base en contient 12, et cela se
  vérifie même sur une base neuve. L'assertion compare donc deux périmètres
  différents ; le corriger proprement suppose de décider qui, du seeder de
  base ou du seeder de corrections, fait autorité sur le total. Question
  produit, laissée ouverte.
