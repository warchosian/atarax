# GEMINI Project Guidelines

Ce projet utilise les outils suivants pour la gestion des modules Python et les commits conventionnels.

## Architecture des Modules

Le projet est organisé en un seul package `app` avec des modules catégorisés :

```
src/
└── app/
    ├── cli/              # CLI principal et framework
    │   ├── main.py       # Point d'entrée de la commande
    │   └── __init__.py
    ├── piag/             # Module RAG PIAG
    │   ├── commands/     # CLI pour les opérations PIAG
    │   ├── core/         # Logique métier PIAG
    │   └── __init__.py
    ├── ocr/              # Module OCR
    │   ├── commands/
    │   ├── core/
    │   └── __init__.py
    ├── scan/             # Module Scanner
    │   ├── commands/
    │   ├── core/
    │   └── __init__.py
    └── conversion/       # Module conversion (PDF, images, compression)
        ├── commands/
        ├── core/
        └── __init__.py
```

### Organisation par Catégories

**`app/cli/`** : Framework CLI principal
- Point d'entrée de la commande `your-project-cli`
- Routage vers les différents modules
- Utilitaires CLI communs
- Gestion de configuration globale

**Modules métier** : `app/piag/`, `app/ocr/`, `app/scan/`, `app/conversion/`
- Chaque module est une catégorie fonctionnelle indépendante
- Structure standardisée : `commands/` et `core/`
- Pas de dépendances croisées entre modules

### Structure Interne d'une Catégorie

Chaque catégorie sous `app/` suit cette structure :

```
app/<categorie>/
├── commands/       # Scripts CLI et points d'entrée
│   ├── cmd_operation1.py
│   ├── cmd_operation2.py
│   └── ...
├── core/          # Logique métier réutilisable
│   ├── config.py   # Gestion de configuration
│   ├── client.py   # Client API/HTTP
│   ├── models.py   # Classes métier
│   └── utils.py    # Utilitaires spécifiques
└── __init__.py    # Exports publics
```

#### Répertoire `commands/`

Contient les modules CLI exécutables via `python -m`. Chaque fichier gère :
- Parsing des arguments CLI avec `argparse`
- Hiérarchie de configuration : CLI > YAML > ENV > Défaut
- Affichage formaté des résultats pour l'utilisateur
- Gestion des erreurs et codes de sortie appropriés
- Invocation des fonctions métier depuis `core/`

#### Répertoire `core/`

Contient la logique métier pure et réutilisable :
- Fonctions métier principales (sans CLI)
- Clients HTTP/API
- Gestion centralisée de la configuration
- Modèles de données et classes métier
- Utilitaires partagés entre commandes
- Code testable indépendamment du CLI

### Exemple : Module PIAG (RAG)

```
src/
└── app/
    ├── __init__.py
    ├── cli/
    │   ├── main.py                # CLI principal, route vers app.piag
    │   └── __init__.py
    └── piag/
        ├── commands/
        │   ├── collection_add.py      # CLI: créer collection
        │   ├── collection_list.py     # CLI: lister collections
        │   ├── doc_upload.py          # CLI: uploader document
        │   └── search.py              # CLI: recherche RAG
        ├── core/
        │   ├── config.py              # Config YAML centralisée
        │   ├── client.py              # Client HTTP PIAG
        │   ├── collections.py         # Logique collections
        │   └── documents.py           # Logique documents
        └── __init__.py                # Exports: create_collection(), etc.
```

**Imports dans le code :**
```python
# Dans app/cli/main.py
from app.piag import create_collection, search_rag

# Dans app/piag/commands/collection_add.py
from app.piag.core.config import load_config
from app.piag.core.client import PIAGClient

# Pour l'utilisateur final (API programmatique)
from app.piag import create_collection, upload_document
```

### Principes de Séparation

1. **Pas de duplication** : Le code commun (config, HTTP, logging) doit être dans `core/`, jamais dupliqué dans `commands/`.

2. **Réutilisabilité** : Les fonctions dans `core/` doivent être utilisables :
   - Par les CLI dans `commands/`
   - Par d'autres modules Python
   - Par des scripts externes
   - Dans des notebooks Jupyter

3. **Testabilité** : La logique métier dans `core/` doit être testable indépendamment du CLI.

4. **Clarté** : Organisation prévisible pour tous les développeurs :
   - Besoin d'une commande CLI → `app/<categorie>/commands/`
   - Besoin de logique métier → `app/<categorie>/core/`
   - Besoin du framework CLI → `app/cli/`

5. **Indépendance** : Chaque catégorie sous `app/` est autonome et n'a pas de dépendances entre catégories.

## Gestion des dépendances Python avec Poetry

[Poetry](https://python-poetry.org/) est utilisé pour la gestion des dépendances et le packaging. Pour commencer :

1.  **Installer Poetry**: Si vous n'avez pas Poetry, suivez le guide d'installation officiel.
2.  **Installer les dépendances**: Naviguez à la racine du projet et exécutez :
    ```bash
    poetry install
    ```
3.  **Vérification avant Build**: Avant de procéder à un `poetry build`, assurez-vous toujours que le fichier `pyproject.toml` contient toutes les dépendances nécessaires et qu'elles sont cohérentes.
4.  **Activer l'environnement virtuel**: Pour activer l'environnement virtuel du projet, exécutez :
    ```bash
    poetry shell
    ```

## Hiérarchie de Configuration

### 🚨 RÈGLE OBLIGATOIRE DU PROJET

**TOUS les modules, commandes et fonctionnalités du projet DOIVENT impérativement respecter la hiérarchie de configuration standardisée définie ci-dessous.**

Cette règle s'applique à :
- ✅ Toutes les nouvelles commandes CLI
- ✅ Tous les nouveaux modules (app/*)
- ✅ Toutes les modifications de commandes existantes
- ✅ Toutes les intégrations d'API externes
- ✅ Toute fonctionnalité nécessitant une configuration

**Aucune exception n'est autorisée sans validation explicite dans les issues du projet.**

### Principe de la Hiérarchie (LOI DU PROJET)

La configuration **DOIT** suivre cet ordre de priorité décroissant, du plus spécifique au plus général :

1. **Arguments CLI** - Priorité la plus haute (OBLIGATOIRE)
2. **Fichier YAML** - Configuration structurée (OBLIGATOIRE)
3. **Variables d'environnement** - Configuration système (OBLIGATOIRE)
4. **Valeurs par défaut** - Priorité la plus basse (OBLIGATOIRE)

**Règle d'écrasement :** Chaque niveau **DOIT** écraser les niveaux inférieurs. Par exemple, un argument CLI écrasera la valeur correspondante dans le fichier YAML, les variables d'environnement et les valeurs par défaut.

### ❌ Anti-Patterns Interdits

Les pratiques suivantes sont **STRICTEMENT INTERDITES** :

```python
# ❌ INTERDIT : Configuration uniquement par arguments CLI
def my_command(url: str, output: str):
    # Pas de support YAML ni variables d'env
    pass

# ❌ INTERDIT : Priorité inversée (YAML écrase CLI)
config = load_yaml()
if cli_arg:
    config['url'] = cli_arg  # FAUX : CLI devrait avoir priorité absolue

# ❌ INTERDIT : Variables d'env non supportées
def my_command(url: str):
    # Impossible de configurer via WIKISI_URL
    pass

# ❌ INTERDIT : Pas de valeurs par défaut
def my_command(url: str = None):
    if url is None:
        raise ValueError("URL required")  # FAUX : doit avoir un défaut
```

### ✅ Pattern Obligatoire

**TOUS les nouveaux modules DOIVENT utiliser ce pattern :**

```python
def my_command(
    url: Optional[str] = None,
    output_dir: Optional[str] = None,
    config_path: Optional[str] = None,
    verbose: bool = False
) -> int:
    """
    Ma commande avec hiérarchie de configuration complète.

    Hiérarchie (du plus au moins prioritaire) :
    1. Arguments CLI (url, output_dir, etc.)
    2. Fichier YAML (config_path)
    3. Variables d'environnement (MY_MODULE_URL, MY_MODULE_OUTPUT_DIR)
    4. Valeurs par défaut
    """
    # 1. Charger configuration (YAML + ENV + Defaults)
    config = load_config(config_path)

    # 2. Appliquer arguments CLI (priorité maximale)
    if url is not None:
        config['url'] = url
    if output_dir is not None:
        config['output_dir'] = output_dir

    # 3. Valider que toutes les valeurs requises sont présentes
    if not config.get('url'):
        print("Error: URL required (via --url, config file, or MY_MODULE_URL)", file=sys.stderr)
        return 1

    # 4. Exécuter la logique métier
    return execute_business_logic(config)
```

### Obligations de Documentation

#### 1. Documentation dans --help (OBLIGATOIRE)

**Chaque commande DOIT impérativement documenter sa hiérarchie de configuration dans son aide (`--help`).**

Pour découvrir les commandes et arguments disponibles pour le CLI du projet :

*   Pour l'aide globale : `your-project-cli --help`
*   Pour l'aide d'un module spécifique (ex: `favorites`) : `your-project-cli favorites --help`
*   Pour l'aide d'une commande spécifique (ex: `favorites parse-html`) : `your-project-cli favorites parse-html --help`


Pour découvrir les commandes et arguments disponibles pour le CLI du projet :

*   Pour l'aide globale : `your-project-cli --help`
*   Pour l'aide d'un module spécifique (ex: `favorites`) : `your-project-cli favorites --help`
*   Pour l'aide d'une commande spécifique (ex: `favorites parse-html`) : `your-project-cli favorites parse-html --help`


**Format obligatoire :**

```bash
your-project-cli my-command --help

Usage: your-project-cli my-command [OPTIONS]

Description de la commande...

Options:
  -u, --url URL         URL à traiter
  -o, --output DIR      Répertoire de sortie
  -c, --config FILE     Fichier de configuration YAML
  -v, --verbose         Mode verbeux
  -h, --help            Afficher cette aide

Hiérarchie de configuration (priorité décroissante):
  1. Arguments CLI (--url, --output, etc.)
  2. Fichier YAML (--config)
  3. Variables d'environnement (MY_MODULE_*)
  4. Valeurs par défaut

Variables d'environnement supportées:
  MY_MODULE_URL         URL à traiter
  MY_MODULE_OUTPUT_DIR  Répertoire de sortie
  MY_MODULE_TIMEOUT     Timeout en secondes
  MY_MODULE_TOKEN       Token d'authentification

Exemples:
  # Via arguments CLI
  your-project-cli my-command --url https://example.com --output ./data

  # Via variables d'environnement
  MY_MODULE_URL=https://example.com your-project-cli my-command

  # Via fichier de configuration
  your-project-cli my-command --config config/my-module.yaml
```

#### 2. Fichiers de Configuration (OBLIGATOIRE)

**Pour chaque nouveau module, vous DEVEZ créer deux fichiers de configuration :**

1. **`config/mon-module.yaml.example`** (VERSIONNÉ dans Git)
2. **`config/mon-module.yaml`** (NON VERSIONNÉ, dans .gitignore)

#### 3. Sécurité des Tokens (OBLIGATOIRE)

- ✅ **OBLIGATOIRE** : Utiliser des variables d'environnement pour les tokens/secrets.
- ✅ **OBLIGATOIRE** : Tous les `config/*.yaml` (sauf `*.example`) DOIVENT être dans `.gitignore`.
- ❌ **INTERDIT** : Commiter ou hardcoder des tokens/secrets.

#### 4. Substitution de Variables dans YAML (OBLIGATOIRE)

La substitution de variables d'environnement avec la syntaxe `${VAR:-default}` est obligatoire.

#### 5. Nommage des Variables d'Environnement (OBLIGATOIRE)

Convention : `{MODULE}_{SECTION}_{PARAMETRE}` en majuscules.

### ✅ Checklist de Conformité (OBLIGATOIRE avant commit)

**Avant CHAQUE commit ajoutant/modifiant une commande ou un module, vérifier :**

- [ ] La commande supporte les 4 niveaux de hiérarchie.
- [ ] Fichier `.yaml.example` créé et `config/*.yaml` dans `.gitignore`.
- [ ] Substitution de variables d'env implémentée.
- [ ] `--help` documente la hiérarchie et les variables d'env.
- [ ] Aucun token/secret hardcodé ou commit.
- [ ] Tests unitaires pour la configuration.

## Gestion des Logs et Affichage Console

**Principe général** : Toute application doit utiliser un gestionnaire de logs centralisé pour l'affichage console et la persistance des erreurs.

#### Configuration des Logs

```python
import logging
from datetime import datetime
from pathlib import Path

timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"{application_name}_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

#### Règles d'Utilisation

1. **Affichage Console** : Utiliser `logger.info()`, pas `print()`.
2. **Logs d'Erreurs** : Utiliser `logger.error(..., exc_info=True)` dans les blocs `except`.
3. **Niveaux de Log** : Utiliser `DEBUG`, `INFO`, `WARNING`, `ERROR` de manière appropriée.
4. **Rotation des Logs** : Utiliser `RotatingFileHandler` pour les applications longue durée.

## Tests et Couverture de Code

### 🚨 RÈGLE OBLIGATOIRE - TESTS

**TOUS les nouveaux modules, commandes et fonctionnalités DOIVENT être couverts par des tests.**

### Objectifs de Couverture (OBLIGATOIRES)

- **Couverture minimale** : 80% du code DOIT être couvert par des tests.
- **Couverture cible** : 90% ou plus pour le code critique.
- **❌ Tout pull request avec une couverture < 80% sera automatiquement rejeté.**

### Obligations Spécifiques pour la Hiérarchie de Configuration

Chaque module doit tester les 4 niveaux de priorité de la configuration.

### Exécution des Tests

```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=app --cov-report=html

# Vérifier le seuil de couverture
poetry run coverage report --fail-under=80
```

### ✅ Checklist de Tests (OBLIGATOIRE avant commit)

- [ ] Tous les tests passent (`pytest`).
- [ ] Couverture de code ≥ 80%.
- [ ] Pas de régression de couverture.
- [ ] Tests écrits pour toute nouvelle fonctionnalité.

## Workflow de Versioning et de Release

Ce projet suit le **Semantic Versioning (SemVer)** et utilise [Commitizen](https://commitizen-tool.github.io/commitizen/) pour automatiser la gestion des versions et la génération du changelog.

### Commits Conventionnels (Conventional Commits)

- `feat:` : Nouvelle fonctionnalité (→ version MINEURE).
- `fix:` : Correction de bug (→ version PATCH).
- `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `chore:`

Un `BREAKING CHANGE:` ou `!` après le type/scope résulte en une version MAJEURE.

### Processus de Release

1.  **Effectuer les modifications**.
2.  **Indexer et Commiter**: `cz commit`
3.  **Créer la nouvelle version**: `cz bump --changelog`
4.  **Générer le build**: `poetry build`
5.  **Vérification Systématique du Build**: `python -m zipfile -l dist/*.whl`
6.  **Pousser les changements**: `git push --follow-tags`

## Conventions Git (OBLIGATOIRE)

### 🚨 RÈGLE - Branche Principale

**Ce projet utilise OBLIGATOIREMENT la branche `main` comme branche principale, et NON `master`.**

Cette règle s'applique à :
- ✅ Tous les nouveaux repositories
- ✅ Toutes les opérations git (push, pull, merge, etc.)
- ✅ Toutes les configurations CI/CD
- ✅ Toutes les documentations et instructions

### Configuration du Repository

Lors de la création d'un nouveau repository ou du renommage de la branche principale :

```bash
# Renommer la branche master en main (si elle existe)
git branch -m master main

# Pousser la branche main sur le remote
git push -u origin main --follow-tags

# Définir main comme branche par défaut (sur GitLab/GitHub)
# GitLab: Settings > Repository > Default Branch > main
# GitHub: Settings > Branches > Default branch > main
```

### Commandes Git Standards

Toutes les commandes git doivent utiliser `main` :

```bash
# Pousser vers main
git push origin main

# Merger une branche vers main
git checkout main
git merge feature-branch

# Rebaser sur main
git rebase main

# Créer une branche depuis main
git checkout -b nouvelle-branche main
```

### ❌ Anti-Patterns Interdits

```bash
# ❌ INTERDIT : Utiliser master
git push origin master
git checkout master

# ✅ CORRECT : Utiliser main
git push origin main
git checkout main
```

## Vérification de l'Intégrité du Build (`.whl`)

Il est crucial de s'assurer que tous les fichiers nécessaires sont inclus dans le build.

### Inclusion des fichiers dans le build

La configuration se trouve dans `pyproject.toml` (`[tool.poetry]` -> `include`).

### Vérifier le contenu du fichier Wheel

```bash
# Lister le contenu du fichier Wheel
python -m zipfile -l dist/*.whl
```
Si un fichier manque, ajustez `pyproject.toml` et reconstruisez.