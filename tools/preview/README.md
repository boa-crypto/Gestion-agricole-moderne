# Aperçu navigable (outillage local)

Reconstitue une instance d'AgriPro servable dans un navigateur, pour un
environnement sans base managée ni sortie réseau : front sur le port 3000
(seule origine exposée), backend sur 8500, le serveur de développement Vite
relayant `/_event` vers le backend.

Rien de cet outillage n'est importé par l'application versionnée : tout est
appliqué à une copie jetable (`/tmp/preview`).

## Mise en route

```bash
tools/preview/bootstrap.sh      # environnement, copie, correctifs, données, compte
tools/preview/start.sh          # front 3000, backend 8500
```

`bootstrap.sh` est idempotent : il recrée la copie, réapplique les correctifs,
réamorce la base de démonstration et conserve le compte existant.

## Ce que les correctifs changent (dans la copie uniquement)

| Fichier | Effet |
| --- | --- |
| `app/menu_database.py` | amorçage de la base de menus neutralisé (service PostgreSQL managé absent) |
| `app/menu_service.py` | `authenticate` / `revoke_session` délégués au magasin SQLite local |
| `app/menu_policy.py` | `resolve_policy` lit ce magasin ; jeton invalide → `PermissionError` |
| `app/server_guard.py` | `require_service` neutralisé (les services métier vérifiés par le socle managé) |
| `app/states/weather_state.py` | `fetch_forecast` neutralisé (Open-Meteo injoignable) |
| `rxconfig.py` | `api_url` fixée sur l'origine publique du port 3000 |
| `.web/vite.config.js` (template) | relais `/_event`, `/_upload`, `/ping`, `/_health` vers le backend |

## Comptes

`preview_auth.py` remplace le service de comptes par un magasin SQLite
(`.preview/data/preview_auth.db`, ignoré par Git) : même règle de mot de passe
(12 à 256 caractères), même dérivation PBKDF2 que la production
(`app.menu_service`), jeton de session en cookie, premier compte administrateur.

Le compte de démonstration est créé par `seed_account.py` :

```bash
AGRI_PRO_PREVIEW_EMAIL=studio@agripro.preview \
AGRI_PRO_PREVIEW_PASSWORD='…' tools/preview/seed_account.py
```

Sans `AGRI_PRO_PREVIEW_PASSWORD`, un mot de passe aléatoire est généré et
affiché une fois. L'écran de connexion permet aussi de créer un compte.

## Contrôles

Les deux scripts Playwright exigent `playwright-core` et `@sparticuz/chromium`
(`npm i` dans un répertoire de travail, puis `NODE_PATH` vers ses
`node_modules` et `LD_LIBRARY_PATH` vers les bibliothèques extraites) :

```bash
node tools/preview/check.js http://127.0.0.1:3000 /tmp/captures
node tools/preview/check-connexion.js http://127.0.0.1:3000 studio@agripro.preview '…' /tmp/captures
```

## Limites assumées

- `reflex-enterprise` exige une authentification : `CI=1` désamorce le contrôle
  de connexion, sans utiliser de jeton.
- Tous les comptes reçoivent le jeu complet de permissions : la matrice de rôles
  réelle dépend du service managé.
- Configuration et Administration lisent encore la base de menus managée : ces
  deux écrans restent partiellement inopérants.
