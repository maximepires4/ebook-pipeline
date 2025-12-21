# Guide des Métadonnées Ebook (EPUB)

Ce document détaille les métadonnées standard (Dublin Core) et spécifiques (OPF/Calibre) nécessaires pour construire une bibliothèque numérique parfaitement triée et identifiée.

## 1. Identification Unique (La Clé)
Ces métadonnées servent à lier le fichier à une fiche livre unique (pour récupérer couverture, résumé, etc.).

| Champ | Balise XML (OPF) | Importance | Description |
| :--- | :--- | :--- | :--- |
| **Identifiant** | `dc:identifier` | **CRITIQUE** | L'empreinte unique du livre. |
| *Type* | `opf:scheme="ISBN"` | **CRITIQUE** | L'ISBN-13 (ex: `9782226494887`) est le standard absolu pour l'identification. |
| **Éditeur** | `dc:publisher` | Haute | Permet de distinguer les éditions (ex: "Albin Michel" vs "Livre de Poche"). |

---

## 2. Tri et Organisation (Le Classement)
Ces métadonnées déterminent l'ordre d'affichage dans les listes. Sans elles, "Victor Hugo" est classé à la lettre **V**.

### Auteur (Creator)
*   **Affichage** : `dc:creator`
    *   *Valeur* : `Yuval Noah Harari`
*   **Tri** : `opf:file-as` (Attribut)
    *   *Valeur* : `Harari, Yuval Noah`
    *   *Rôle* : Permet le tri par Nom de famille.

### Titre (Title)
*   **Affichage** : `dc:title`
    *   *Valeur* : `Les Misérables`
*   **Tri** : `opf:file-as` (Attribut - optionnel mais recommandé)
    *   *Valeur* : `Miserables, Les`
    *   *Rôle* : Permet d'ignorer les articles définis/indéfinis lors du tri.

### Séries (Sagas)
Le standard Dublin Core ne gère pas nativement les séries. On utilise souvent des balises `<meta>` personnalisées (standard de facto Calibre).
*   **Nom de la série** : `<meta name="calibre:series" content="Harry Potter"/>`
*   **Index** : `<meta name="calibre:series_index" content="1.0"/>`

---

## 3. Découverte et Navigation
Pour la recherche, le filtrage et l'expérience utilisateur.

| Champ | Balise XML | Description |
| :--- | :--- | :--- |
| **Sujets / Tags** | `dc:subject` | Mots-clés multiples (ex: "Histoire", "Science", "Anthropologie"). |
| **Langue** | `dc:language` | Code ISO (ex: `fr`, `en-US`). Essentiel pour filtrer par langue. |
| **Date** | `dc:date` | Date de publication (souvent juste l'année ou YYYY-MM-DD). |
| **Description** | `dc:description` | Le résumé ou la quatrième de couverture. |

---

## Résumé Technique pour l'Implémentation

Lors de l'analyse d'un fichier EPUB, la priorité d'extraction doit être :

1.  **Récupérer `dc:identifier` où `scheme="ISBN"`** -> C'est la source de vérité.
2.  **Récupérer `dc:creator` ET son attribut `opf:file-as`** -> Pour construire un index d'auteurs propre.
3.  **Récupérer `meta name="calibre:series"`** -> Pour regrouper les tomes.
