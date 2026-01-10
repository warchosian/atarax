# NEXT STEPS - Atarax Project Roadmap

Ce document liste les fonctionnalités futures envisagées pour le projet Atarax, organisées par priorité et par module.

## Module Favorites - Gestion des Favoris

### ✅ Fonctionnalités Implémentées (v0.1.0)

1. **favorites-to-md** : Conversion de favoris HTML vers différents formats de visualisation
   - PlantUML Mindmap (.mindmap.puml.md)
   - PlantUML Tree (.tree.puml.md)
   - Mermaid Mindmap (.mermaid.md)
   - Monospace tree (.monospace.md)
   - Stars tree (.stars.md)
   - Fillers tree (.fillers.md)

2. **favorites-organize** : Réorganisation sémantique automatique des favoris
   - Classification automatique par catégories (Personal, Work, AI & Technology, etc.)
   - Règles sémantiques configurables
   - Déduplication des URLs
   - Nettoyage des titres

### 🚀 Fonctionnalités Planifiées

#### Priorité 1 - Gestion des Doublons

**Commande** : `atarax favorites-deduplicate`

**Objectif** : Détecter et supprimer les favoris en double

**Fonctionnalités** :
- Détection des doublons par URL exacte
- Détection des doublons par URL similaire (avec/sans www, http/https)
- Détection des doublons par titre similaire (distance de Levenshtein)
- Modes de traitement :
  - `--dry-run` : Afficher les doublons sans supprimer
  - `--auto` : Supprimer automatiquement (garder le plus récent)
  - `--interactive` : Demander pour chaque doublon
- Critères de conservation :
  - Plus récent (ADD_DATE)
  - Avec icône vs sans icône
  - Titre le plus complet

**Arguments CLI** :
```bash
atarax favorites-deduplicate input.html -o cleaned.html
atarax favorites-deduplicate input.html --dry-run
atarax favorites-deduplicate input.html --interactive
atarax favorites-deduplicate input.html --similarity-threshold 0.9
```

**Configuration YAML** :
```yaml
deduplicate:
  similarity_threshold: 0.9  # 0.0 (différent) à 1.0 (identique)
  keep_newest: true
  keep_with_icon: true
  interactive: false
```

#### Priorité 2 - Fusion de Favoris

**Commande** : `atarax favorites-merge`

**Objectif** : Fusionner plusieurs fichiers de favoris HTML en un seul

**Fonctionnalités** :
- Fusion de 2+ fichiers de favoris
- Gestion des conflits de noms de dossiers
- Déduplication automatique des URLs
- Stratégies de fusion :
  - `merge` : Fusionner les dossiers de même nom
  - `prefix` : Préfixer chaque fichier par son nom
  - `separate` : Créer un dossier par fichier source
- Préservation des métadonnées (dates, icônes)

**Arguments CLI** :
```bash
atarax favorites-merge file1.html file2.html file3.html -o merged.html
atarax favorites-merge *.html -o all-favorites.html --strategy merge
atarax favorites-merge work.html personal.html --strategy separate
```

**Configuration YAML** :
```yaml
merge:
  strategy: merge  # merge, prefix, separate
  deduplicate: true
  conflict_resolution: newest  # newest, oldest, keep_both
```

#### Priorité 3 - Recherche et Filtrage

**Commande** : `atarax favorites-search`

**Objectif** : Rechercher et filtrer des favoris selon différents critères

**Fonctionnalités** :
- Recherche par mot-clé (titre, URL)
- Recherche par expression régulière
- Filtrage par date (avant/après, plage)
- Filtrage par domaine
- Filtrage par dossier
- Export des résultats :
  - HTML (favoris filtrés)
  - JSON (données structurées)
  - CSV (tableau)
  - Markdown (liste)

**Arguments CLI** :
```bash
atarax favorites-search input.html --query "python"
atarax favorites-search input.html --domain "github.com"
atarax favorites-search input.html --after 2024-01-01 --before 2024-12-31
atarax favorites-search input.html --folder "Work" -o work-bookmarks.html
atarax favorites-search input.html --regex "tutorial|guide" --format json
```

**Configuration YAML** :
```yaml
search:
  case_sensitive: false
  match_title: true
  match_url: true
  output_format: html  # html, json, csv, markdown
```

#### Priorité 4 - Statistiques et Analyse

**Commande** : `atarax favorites-stats`

**Objectif** : Générer des statistiques et analyses sur les favoris

**Fonctionnalités** :
- Statistiques générales :
  - Nombre total de favoris
  - Nombre de dossiers
  - Profondeur maximale de l'arborescence
  - Doublons détectés
- Analyses par domaine :
  - Top 10 domaines les plus fréquents
  - Distribution par TLD (.com, .fr, .org, etc.)
- Analyses temporelles :
  - Favoris par année/mois
  - Période la plus active
- Analyses de structure :
  - Dossiers les plus remplis
  - Dossiers vides
  - Favoris orphelins (hors dossiers)
- Formats de sortie :
  - Texte formaté
  - JSON
  - HTML avec graphiques (Chart.js)

**Arguments CLI** :
```bash
atarax favorites-stats input.html
atarax favorites-stats input.html --format json -o stats.json
atarax favorites-stats input.html --format html -o report.html
atarax favorites-stats input.html --top-domains 20
```

**Configuration YAML** :
```yaml
stats:
  output_format: text  # text, json, html
  top_domains_count: 10
  include_charts: true
  group_by_year: true
```

#### Priorité 5 - Validation et Nettoyage

**Commande** : `atarax favorites-validate`

**Objectif** : Valider les favoris et détecter les problèmes

**Fonctionnalités** :
- Vérification des URLs :
  - URLs cassées (HTTP 404, timeout)
  - URLs invalides (malformées)
  - Redirections
- Vérification de structure :
  - Dossiers vides
  - Profondeur excessive
  - Titres manquants ou invalides
- Rapport de validation :
  - Liste des problèmes détectés
  - Suggestions de correction
  - Niveau de sévérité (error, warning, info)

**Arguments CLI** :
```bash
atarax favorites-validate input.html
atarax favorites-validate input.html --check-urls
atarax favorites-validate input.html --timeout 5 --format json
atarax favorites-validate input.html --severity error
```

**Commande** : `atarax favorites-clean`

**Objectif** : Nettoyer automatiquement les favoris

**Fonctionnalités** :
- Suppression des URLs cassées
- Suppression des dossiers vides
- Normalisation des titres
- Nettoyage des URLs (suppression paramètres de tracking)
- Consolidation de l'arborescence

**Arguments CLI** :
```bash
atarax favorites-clean input.html -o cleaned.html
atarax favorites-clean input.html --remove-broken-urls
atarax favorites-clean input.html --remove-empty-folders
atarax favorites-clean input.html --normalize-titles
atarax favorites-clean input.html --remove-tracking-params
```

**Configuration YAML** :
```yaml
clean:
  remove_broken_urls: true
  remove_empty_folders: true
  normalize_titles: true
  remove_tracking_params: true
  tracking_params: ["utm_source", "utm_medium", "utm_campaign", "fbclid"]
```

#### Priorité 6 - Configuration YAML Avancée

**Objectif** : Implémenter le support complet de la configuration YAML pour tous les modules

**Fonctionnalités** :
- Configuration centralisée dans `config/favorites.yaml`
- Règles de catégorisation personnalisables pour `favorites-organize`
- Templates personnalisables pour `favorites-to-md`
- Paramètres par défaut pour toutes les commandes
- Profils de configuration multiples

**Structure de configuration** :
```yaml
# config/favorites.yaml

# Configuration globale
favorites:
  default_output_dir: "./output"
  encoding: "utf-8"
  verbose: false

# Configuration favorites-organize
organize:
  category_rules:
    - keywords: ["python", "django", "flask"]
      category: "Development/Backend/Python"
    - keywords: ["react", "vue", "angular"]
      category: "Development/Frontend/JavaScript"
    - domains: ["github.com", "gitlab.com"]
      category: "Development/Tools/Git"
  blacklisted_folders: ["Nouveau dossier", "url", "This", "New"]

# Configuration favorites-to-md
to_md:
  default_format: "mindmap"
  header_template: "# {title} - Export Date: {date}\n\n"
  max_title_length: 80

# Configuration favorites-deduplicate
deduplicate:
  similarity_threshold: 0.9
  keep_newest: true
  interactive: false

# Configuration favorites-merge
merge:
  strategy: "merge"
  deduplicate: true
  conflict_resolution: "newest"

# Configuration favorites-search
search:
  case_sensitive: false
  output_format: "html"

# Configuration favorites-stats
stats:
  output_format: "text"
  top_domains_count: 10
  include_charts: true

# Configuration favorites-clean
clean:
  remove_broken_urls: true
  remove_empty_folders: true
  remove_tracking_params: true
  tracking_params: ["utm_source", "utm_medium", "utm_campaign", "fbclid", "gclid"]
```

**Arguments CLI communs** :
```bash
# Utiliser une configuration spécifique
atarax favorites-organize input.html -c config/work.yaml

# Utiliser un profil spécifique
atarax favorites-organize input.html --profile work
```

### 🎯 Roadmap par Version

#### v0.2.0 - Gestion Avancée
- ✅ favorites-organize
- 🚀 favorites-deduplicate
- 🚀 Support YAML pour favorites-organize

#### v0.3.0 - Fusion et Recherche
- 🚀 favorites-merge
- 🚀 favorites-search

#### v0.4.0 - Analyse et Validation
- 🚀 favorites-stats
- 🚀 favorites-validate
- 🚀 favorites-clean

#### v0.5.0 - Configuration Complète
- 🚀 Support YAML complet pour tous les modules
- 🚀 Profils de configuration multiples
- 🚀 Templates personnalisables

## Autres Modules Futurs

### Module PIAG (RAG)
- Gestion de collections de documents
- Recherche sémantique avec RAG
- Intégration avec différents LLM

### Module OCR
- Extraction de texte depuis images
- Support multi-langues
- Formats de sortie multiples

### Module Scan
- Numérisation de documents
- Optimisation automatique
- Détection de pages

### Module Conversion
- Conversion PDF ↔ Images
- Compression intelligente
- Fusion/Séparation de PDF

## Contributions

Pour proposer de nouvelles fonctionnalités ou contribuer au développement, consultez le fichier CONTRIBUTING.md (à créer).

## Légende

- ✅ Implémenté
- 🚀 Planifié
- 💡 Idée en réflexion
- 🔧 En développement
