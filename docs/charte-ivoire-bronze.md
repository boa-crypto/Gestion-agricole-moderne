# Charte « Ivoire & Bronze »

La charte d'AgriPro reprend le registre visuel du site de référence fourni
(`parklanecph.com`) : ivoire chaud, encre profonde, filets d'un pixel,
typographie d'apparat et animations lentes. Le thème sombre d'origine
(« Encre & Chlorophylle ») reste disponible sous le nom **encre**.

> Le CSS, les polices et les images de `parklanecph.com` n'ont pas pu être
> téléchargés depuis l'environnement de travail (seuls GitHub, npm et PyPI
> sortent du bac à sable). La charte ci-dessous est donc une **reconstruction
> documentée** à partir de ce qui était observable du site : structure
> éditoriale, hiérarchie typographique, micro-libellés capitales très espacés,
> filets fins, boutons sobres, animations lentes. Aucune capture ni police
> propriétaire n'a été copiée.

## 1. Deux thèmes, un seul jeu de jetons

Chaque couleur est déclarée deux fois, en canaux RVB, dans `app/components/design.py` :

```css
:root { --ap-paper-rgb: 26 25 18; /* ivoire */ }
[data-theme="dark"] { --ap-paper-rgb: 242 239 228; /* encre */ }
```

Les classes Tailwind les consomment avec une opacité :

```
text-[rgb(var(--ap-paper-muted-rgb)/0.86)]
border-[rgb(var(--ap-paper-rgb)/0.18)]
```

Le basculement se fait sans rechargement ni état serveur : l'attribut
`data-theme` est posé sur `<html>` par le script `THEME_BOOTSTRAP`, mémorisé
dans `localStorage` (`agripro-theme`) et actionné par le bouton
`theme_toggle()` du bandeau supérieur.

## 2. Rôles de couleur

| Jeton | Ivoire | Encre | Usage |
| --- | --- | --- | --- |
| `ink` | `#F7F4EC` | `#0A0A08` | fond de page |
| `surface`, `surface-raised`, `surface-high` | `#FAF8F1` → `#E9E3D5` | `#101208` → `#191C13` | panneaux, cartes, champs |
| `paper` | `#1A1912` | `#F2EFE4` | texte principal |
| `paper-muted` | `#48453C` | `#C9C5B4` | texte secondaire |
| `paper-faint` | `#666258` | `#8F8C7E` | mentions, légendes |
| `accent` | `#1B1A14` | `#D8FA5E` | bouton plein, marqueurs actifs |
| `bronze` | `#966E3C` | — | filets et accents chauds |
| `flame` / `danger` | `#A83F21` / `#B0412F` | `#FF5A2B` / `#FF6B5A` | alertes, retards |
| `sage` | `#5F7350` | `#A9C98B` | conduite biologique, succès |
| `info` | `#46658A` | `#9CC3FF` | information, contexte |

Les teintes s'inversent : en thème clair, l'accent devient encre (bouton plein
noir, texte ivoire) ; en thème sombre, il redevient chlorophylle.

## 3. Typographie

| Rôle | Police | Réglage |
| --- | --- | --- |
| Registre éditorial | Cormorant Garamond 300 | `.ap-serif`, `.ap-display` ; interlignage 0.92, approche −0.014 em |
| Lecture et interface | Inter Tight 300–600 | corps 13 px, approche −0.012 em |
| Micro-libellés | Inter Tight 500 | `.ap-eyebrow` : 10 px, capitales, approche 0.34 em |
| Chiffres | Inter Tight tabulaire | `.ap-mono` (alignement des colonnes) |

## 4. Composants

- **Boutons** : deux registres seulement — plein encre (action principale,
  capitales espacées, hauteur 40 px, angles vifs) et filet (action secondaire).
  Aucun dégradé, aucune ombre portée, aucun arrondi.
- **Menus** : filets d'un pixel, item actif signalé par un fond très légèrement
  plus dense et une barre latérale ; liens de navigation dotés d'un filet qui se
  trace au survol (`.ap-link`).
- **Cartes** : fond de surface, filet supérieur, aucune élévation.
- **États** : vides, chargement (squelettes à balayage) et erreurs conservés à
  l'identique, simplement recomposés dans la nouvelle palette.

## 5. Mouvement

| Animation | Durée | Courbe |
| --- | --- | --- |
| Apparition `ap-rise` | 900 ms | `cubic-bezier(.16,.84,.44,1)` |
| Séquence `ap-stagger` | 820 ms, pas de 70 ms | idem |
| Filet de lien `ap-link` | 420 ms | idem |
| Zoom d'image `ap-zoom` | 900 ms | idem |
| Feuille / notification | 260 ms / 220 ms | idem |

`prefers-reduced-motion: reduce` neutralise toutes les animations et
transitions.

## 6. Mise en œuvre

- `rxconfig.py` : `vite_allowed_hosts=True` pour que l'aperçu de la plateforme
  (`*.e2b.app`) ne reçoive plus de 403 du serveur de développement Vite.
- `reflex.lock/package.json` : l'override `postcss` incompatible avec la version
  épinglée par Reflex 0.10 a été retiré (le démarrage échouait en `EOVERRIDE`).
- Aucun secret, aucune police propriétaire, aucun actif distant n'est versionné.
