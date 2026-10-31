# Parcours des routes — validation du 31 octobre 2026

Parcours automatisé des seize routes protégées, en 1440 × 1000, sur l'aperçu
local (`reflex run`, ports 3000 et 8000). Le script est versionné dans
`scripts/tools/route_tour.js` ; il exige `playwright-core` et
`@sparticuz/chromium`, installés hors dépôt.

```powershell
node scripts/tools/route_tour.js http://127.0.0.1:3000 rapport.json 4000
```

## Résultat

**16 routes sur 16 répondent 200** et rendent leur héros.

| Route | Statut | Titre rendu |
| --- | --- | --- |
| `/` | 200 | Cockpit agronomique |
| `/configuration` | 200 | Configuration & accès |
| `/parcelles` | 200 | Parcelles & cultures |
| `/referentiel` | 200 | Catégorie → Culture → Espèce → Variété |
| `/phenologie` | 200 | — (squelette de chargement) |
| `/traitements` | 200 | Traitements & récoltes |
| `/employes` | 200 | Employés & compétences |
| `/maintenance` | 200 | Engins & maintenance |
| `/cartographie` | 200 | Cartographie interactive |
| `/rapports` | 200 | État phénologique de l'exploitation |
| `/charges` | 200 | Charges & dépenses |
| `/crm` | 200 | CRM & Partenaires |
| `/recherche` | 200 | Recherche globale |
| `/guide` | 200 | Guide Agricole AgriPro |
| `/administration` | 200 | Utilisateurs, rôles & permissions |
| `/audit` | 200 | Cartographie AgriPro ↔ Guide |

`/phenologie` n'affiche pas de titre au moment de la mesure : sa page était en
squelette. La cause est identifiée et corrigée (import paresseux de
`reflex.model` bloquant la boucle d'événements, voir `docs/rapport-final-2026.md`
§10) ; la page rend désormais son contenu (11 profils, 88 stades).

### Panneaux CRM en accès direct (lot 10)

Le CRM tient sur une route unique `/crm` ; l'onglet est porté par la requête
(`?cockpit=commercial&vue=…`). Vérifié à la capture, en arrivant par l'URL, sans
navigation préalable :

| URL | Contenu attendu | Constaté |
| --- | --- | --- |
| `/crm?cockpit=commercial&vue=ventes` | registre des ventes | 3 pièces, HT 27 496 800 · TVA 5 224 392 · TTC 32 721 192 DA, réglé 23 802 475, reste dû 8 918 717 |
| `/crm?cockpit=commercial&vue=clients` | espace clients | 3 tiers, fiche « Coopérative Dattes El Oued » ouverte, indicateurs clients renseignés |
| `/crm?cockpit=financier&vue=creances` | registre des créances | 3 lignes, TTC 32 721 192, reste dû 8 918 717 |
| `/crm?cockpit=achats&vue=fournisseurs` | espace fournisseurs | 5 tiers, fiche « Atelier Mécanique Batna SARL » ouverte |

Chaque onglet appartient à un cockpit : `vue=creances` sous `cockpit=commercial`
retombe sur la vue générale, comportement normal de `resolve_navigation_entry`.

Un onglet absent du cockpit demandé (`vue=achats` sous `cockpit=commercial`)
retombe sur la vue générale : c'est le comportement de `resolve_navigation_entry`,
inchangé.

## Erreurs console

Quatre messages, identiques sur les seize routes, tous imputables à l'aperçu
et non au code applicatif :

| Message | Origine | Portée |
| --- | --- | --- |
| `Failed to load resource: net::ERR_CONNECTION_CLOSED` | WebSocket `/_event` coupé par le navigateur sans interface au moment de la fermeture de page | aperçu |
| `Encountered a script tag while rendering React component` | injection du cookie de session par `preview_boot.py`, hors dépôt | aperçu |
| `Unexpected token '<'` | premier chargement du bundle pendant la reconstruction Vite | aperçu |
| `Hydration failed because the server rendered text didn't match the client` | le rendu serveur part d'un état neutre, le client hydrate avec la politique simulée | aperçu |

Aucune erreur ne provient d'un composant de `app/` : les quatre messages
apparaissent aussi sur une page blanche servie par le même montage.

## À refaire hors aperçu

Sur un déploiement réel (session réelle, un seul serveur), ces quatre messages
doivent disparaître. Si l'erreur d'hydratation persiste, elle signalera un
écart réel entre l'état serveur et l'état client — c'est le seul des quatre à
surveiller.
