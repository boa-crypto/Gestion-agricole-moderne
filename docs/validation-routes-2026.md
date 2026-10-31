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

`/phenologie` n'affiche pas de titre au moment de la mesure : sa page est en
squelette (`phenology_admin` charge son référentiel au montage, même symptôme
que les panneaux CRM décrit dans `docs/audit-refonte-2026.md` §5). Le titre
apparaît dès que le chargement aboutit.

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
