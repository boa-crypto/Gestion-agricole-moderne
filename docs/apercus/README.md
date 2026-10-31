# Aperçus — refonte « Encre & Chlorophylle »

Captures de l'application AgriPro après la refonte éditoriale, prises sur
l'application réelle (Reflex + base SQLite de démonstration), au format
1440 × 1050 @2x et 390 × 844 @2x.

| Fichier | Page | État des données |
| --- | --- | --- |
| `01-cockpit-agronomique.jpg` | `/` — cockpit | jeu de démonstration complet |
| `02-crm-synthese.jpg` | `/crm?cockpit=commercial&vue=synthese` | clients, fournisseurs et ventes peuplés |
| `03-parcelles.jpg` | `/parcelles?cockpit=agricole` | listes en chargement (seeder non rejoué) |
| `04-guide.jpg` | `/guide?cockpit=documentaire` | guide vide, structure visible |
| `05-referentiel.jpg` | `/referentiel?cockpit=agricole` | référentiel vide, structure visible |
| `06-cartographie.jpg` | `/cartographie?cockpit=cartographique` | page pas encore migrée vers les primitives |
| `07-cockpit-mobile.jpg` | `/` en 390 px | jeu de démonstration complet |

`index.html` est la galerie commentée (à ouvrir dans un navigateur) ; elle
ajoute le propos de chaque double page et signale les états vides.

Les aperçus ont été produits dans un environnement de prévisualisation sans
PostgreSQL ni jeton `reflex-enterprise` : la session est simulée par un cookie
de démonstration et le chargement météo externe est indisponible. Certaines
pages s'affichent donc dans leur état de chargement, ce qui ne reflète pas le
rendu une fois les données chargées en production.
