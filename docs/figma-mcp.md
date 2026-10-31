# MCP Figma — installation, vérification, capacités

Ce document consigne la procédure **officielle** (documentation Figma, consultée
le 31 octobre 2026) et le diagnostic exact de l'environnement d'exécution de
l'agent. Aucune installation n'est simulée : l'état réel est indiqué section 1.

Références :

- <https://developers.figma.com/docs/figma-mcp-server/>
- <https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/>
- <https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/>

## 1. Diagnostic de l'environnement de l'agent

Commandes exécutées dans l'espace de travail et résultats bruts :

| Vérification | Commande | Résultat |
| --- | --- | --- |
| Node.js | `node -v` | `v22.22.3` |
| npm | `npm -v` | `10.9.8` |
| Claude Code | `command -v claude` | **absent** |
| Configuration MCP | `ls ~/.claude.json ~/.config/claude` | **aucune** |
| Accès `https://mcp.figma.com/mcp` | `curl -s -o /dev/null -w "%{http_code}"` | **`000`** (connexion refusée : sortie réseau filtrée) |
| Accès `https://api.figma.com/v1/me` | idem | **`000`** |
| Système | `uname -a` | Linux `e2b.local` 6.1 |

**Conclusion honnête : l'installation ne peut pas être réalisée depuis cet
espace de travail.** Trois blocages cumulatifs :

1. Le binaire `claude` n'existe pas ici : aucune configuration MCP de Claude
   Code ne peut être écrite ni rechargée.
2. La sortie réseau est limitée à quelques hôtes (`github.com`,
   `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`,
   `files.pythonhosted.org`) : `mcp.figma.com` et `api.figma.com` sont
   injoignables, donc l'authentification OAuth et les appels d'outils sont
   impossibles.
3. L'authentification Figma exige **ton** navigateur et **ton** compte : elle ne
   peut pas être déléguée à un agent distant.

Aucune commande d'installation n'a donc été lancée, et aucun serveur MCP n'est
déclaré opérationnel. La suite de ce document est la procédure à exécuter sur ta
machine Windows.

## 2. Installation recommandée — plugin Figma pour Claude Code

C'est la méthode recommandée par Figma : le plugin embarque la configuration du
serveur MCP **et** les skills Figma (fiabilité accrue, notamment pour l'écriture
sur le canevas).

```powershell
# 1. Vérifier Claude Code
claude --version

# 2. Installer le plugin officiel
claude plugin install figma@claude-plugins-official

# 3. Redémarrer Claude Code, puis dans la session :
#    /plugin  → onglet « Installed » → figma → Entrée → Entrée
#    Le navigateur s'ouvre : « Allow access »
#    /plugin à nouveau : le serveur figma apparaît « connected »
```

Si l'organisation bloque les plugins, utiliser la méthode manuelle.

## 3. Installation manuelle du serveur distant (OAuth)

```powershell
# Portée utilisateur : disponible dans tous les projets
claude mcp add --scope user --transport http figma https://mcp.figma.com/mcp

# Ou portée projet (écrit .mcp.json à la racine du dépôt)
claude mcp add --transport http figma https://mcp.figma.com/mcp

# Puis, dans une nouvelle session Claude Code :
#   /mcp → figma → Authenticate → « Allow access » dans le navigateur
#   Attendu : « Authentication successful. Connected to figma »
#   Vérifier avec /mcp
```

L'authentification est un **OAuth navigateur** : aucun jeton n'est à copier,
aucun secret n'est écrit dans le dépôt. Claude Code stocke le jeton dans son
propre magasin d'identifiants, hors du projet.

Équivalent `.mcp.json` (si tu préfères versionner la déclaration **sans secret**
dans le dépôt) :

```json
{
  "mcpServers": {
    "figma": {
      "type": "http",
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

Ne jamais ajouter d'en-tête `Authorization` en clair dans ce fichier.

## 4. Variante serveur local (bureau)

Réservée aux besoins d'organisation : nécessite l'application **Figma desktop**
et une licence Dev ou Full (plan Professional, Education, Organization,
Government ou Enterprise). Le serveur local n'offre pas les outils marqués
« Remote only ». Pour un poste de développement standard, la méthode des
sections 2–3 suffit.

## 5. Vérification réelle de la connexion

Après authentification :

```powershell
claude mcp list          # figma doit apparaître « connected »
# dans la session :
#   /mcp                 # état et outils exposés
```

Premier test utile (outil de compte, sans toucher à un fichier) :

```text
Demande à l'agent : « utilise whoami et donne mon plan Figma et mon siège »
```

Puis un test de lecture, sur n'importe quelle frame :

```text
« Ouvre <lien Figma>, liste les frames de la page et donne-moi
get_metadata de la frame sélectionnée, puis get_screenshot »
```

Attendu : un plan XML allégé + une capture. Si `whoami` répond mais que la
lecture d'un fichier échoue, le problème est un **droit d'accès au fichier**
(partage, siège), pas la connexion.

## 6. Outils réellement exposés par le serveur distant

Lecture (extrait vérifié de la documentation officielle) :

| Outil | Usage |
| --- | --- |
| `whoami` | identité, plan, siège |
| `get_metadata` | plan XML allégé d'une sélection |
| `get_design_context` | contexte de design + code d'un calque |
| `get_screenshot` | capture d'une sélection |
| `get_variable_defs` | variables et styles utilisés |
| `get_code_connect_map` | correspondances Code Connect |
| `search_design_system` | recherche dans les bibliothèques |
| `get_libraries` | bibliothèques souscrites |
| `download_assets` | export d'images et sources |
| `get_motion_context` | données d'animation (keyframes) |
| `get_figjam` | conversion d'un diagramme FigJam |

Écriture (serveur distant uniquement, siège Full requis pour écrire hors
brouillons) : `create_new_file`, `create_design_system_rules`,
`add_code_connect_map`, et les outils de canevas accompagnés des skills Figma.

**Distinction à retenir** : le MCP permet de **créer et modifier du contenu
natif Figma** via le serveur distant + skills, mais **pas de piloter l'interface
Figma** (pas de clic, pas de prototype interactif). Les capacités d'écriture
sont en bêta et facturées à l'usage à terme.

## 7. Dépannage Windows / PowerShell

| Symptôme | Cause probable | Correctif |
| --- | --- | --- |
| `claude : impossible de charger le fichier` | script PS non signé / politique d'exécution | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` puis rouvrir PowerShell |
| `claude` inconnu après installation npm | `%APPDATA%\npm` absent du `PATH` | ajouter `%APPDATA%\npm` au `PATH` utilisateur, relancer le terminal |
| `/mcp` affiche « failed » | proxy d'entreprise | `$env:HTTPS_PROXY="http://proxy:port"` avant de lancer `claude` |
| `Allow access` renvoie une erreur 403 | siège Viewer sur le fichier | demander un siège Dev, ou partager le fichier avec droit de lecture |
| Outils présents mais lecture vide | aucun fichier ouvert / sélection vide | sélectionner une frame dans Figma, puis relancer la demande |
| Plugin bloqué | politique d'administration | passer à la méthode manuelle (section 3) |

## 8. Ce qui a été fait à la place, ici

Faute d'accès Figma, la mission a été poursuivie selon la branche « aucun
fichier Figma » prévue par le brief :

1. `docs/design-tokens.json` — jetons au format Tokens Studio, importables dans
   Figma (styles de couleur, typographie, espacements, rayons).
2. `docs/editorial-design.md` §§ 1–8 — direction artistique, échelle
   typographique, grille, composants, états, mouvement.
3. Le code implémente ces jetons : `app/components/design.py`.

Dès que le MCP est connecté sur ta machine, la comparaison visuelle devient
possible : `get_screenshot` d'une frame vs capture de l'application, puis
`get_variable_defs` pour aligner les variables Figma sur `design.py`.
