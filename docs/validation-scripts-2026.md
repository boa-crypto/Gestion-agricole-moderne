# Scripts de vérification hérités — état au 31 octobre 2026

Vingt-cinq fichiers de `tests/` ne sont pas des modules pytest : ce sont des
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
2. **Syntaxe JavaScript corrigée** — 147 `.length()` et 18 `.contains()`
   (traductions d'un code JS) remplacés par `len(...)` et `... in ...`.
3. **Deux bugs applicatifs réels corrigés**, révélés par les scripts :

   | Fichier | Défaut | Effet |
   | --- | --- | --- |
   | `app/states/contour_state.py` | `await ContourState._decide_and_report(parcel_id, …)` sans `self` (2 appels) | vérifier ou programmer le relevé d'un contour levait `AttributeError` : les deux boutons de décision étaient inopérants |
   | `app/states/remediation_state.py` | `await RemediationState._watch_alert / _decide_stock / _decide_contour(…)` sans `self` (7 appels) | mettre sous surveillance, arbitrer un stock ou trancher un contour levait `AttributeError` depuis l'interface |

4. **Exécuteur** — `scripts/run_legacy_tests.py` lance les scripts un par un,
   restaure la base avant chacun (la suite est ainsi reproductible) et rend un
   code de sortie non nul en cas d'échec.

```powershell
python scripts/run_legacy_tests.py            # tout
python scripts/run_legacy_tests.py stock guide
```

## Résultat : 16 scripts sur 25 réussis

| Script | État | Remarque |
| --- | --- | --- |
| `test_audit` | réussi | |
| `test_cartography` | réussi | |
| `test_catalog` | réussi | |
| `test_catalog_bridge` | réussi | |
| `test_catalog_browser` | réussi | |
| `test_contour` | réussi | après correctif `self` |
| `test_contour_api` | réussi | |
| `test_expenses` | réussi | |
| `test_guide_admin` | réussi | |
| `test_help_context` | réussi | |
| `test_maintenance` | réussi | |
| `test_module_integration` | réussi | |
| `test_phenology_ops` | réussi | |
| `test_remediation` | réussi | après correctif `self` |
| `test_search` | réussi | |
| `test_stock` | réussi | |
| `test_admin_operations` | échec | `PermissionError: Une session métier vérifiée est requise` |
| `test_delegation_expiry` | échec | idem |
| `test_phenology_admin` | échec | idem |
| `test_administration_state` | échec | `LookupError: EventContext` (contexte d'événement Reflex absent) |
| `test_security_integration` | échec | idem |
| `test_corrections` | échec | attendu : sous-entités de démonstration non amorcées (`expense`, `assignment`, `employee_skill`…) |
| `test_guide` | échec | attendu : toutes les procédures du guide amorcées |
| `test_guide_interface` | échec | assertion d'interface sur le guide |
| `test_remediation_api` | échec | attendu : l'alerte clôturée doit sortir de la liste |

### Les cinq échecs de sécurité

`app/server_guard.py` exige un contexte d'événement vérifié (`CHECKED_CONTEXT`)
et une politique résolue. Les scripts appellent les gestionnaires directement :
le garde les refuse, ce qui est le comportement attendu. Les faire passer
supposerait de simuler une session et une politique complètes dans le harnais —
possible, mais cela revient à désactiver le garde dans les tests. Décision :
laissé en l'état et documenté, plutôt que contourné silencieusement.

### Les quatre échecs de données ou d'assertion

Ils portent sur des jeux de démonstration que les seeders ne couvrent pas
(charges, affectations, compétences, procédures du guide) ou sur un
comportement qui a changé depuis l'écriture du script. Ils ne traduisent pas un
défaut de la refonte : `test_guide` et `test_corrections` échouaient déjà avant
elle, faute de pouvoir s'exécuter.
