# AsteriaCLI

> **Your single command-line interface for managing all AI-related workflows.**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-orange.svg)](https://peps.python.org/pep-0008/)

## Repository

The official source code lives at:

```text
https://github.com/indrajit912/AsteriaCLI.git
```

Feel free to star, fork, and contribute!

---

## Overview

AsteriaCLI is a production-quality Python CLI application designed to manage all AI-related
workflows from a single, beautiful, unified interface. Built with extensibility in mind, it
uses a plugin-like architecture so new AI providers can be added with zero changes to existing
code.

**Developer:** Indrajit Ghosh  
**Affiliation:** Postdoctoral Researcher, IIT Kanpur  
**Copyright:** © 2026–Present Indrajit Ghosh. All Rights Reserved.

---

## Features

| Feature | Description |
|---------|-------------|
| 🤖 **Agy Module** | Manage Gemini Antigravity CLI conversations with rich tables, tagging, fuzzy search, and JSON/CSV export |
| 🔮 **Gemini Module** | Full workspace → project → prompt → output lifecycle with Gemini API integration |
| 🗄️ **SQLite + SQLAlchemy** | Robust relational database with UUID primary keys and timestamps |
| 🎨 **Rich UI** | Beautiful panels, tables, progress bars, syntax highlighting, spinners |
| 🔌 **Plugin Architecture** | Add Claude, OpenAI, Ollama, DeepSeek with zero changes to existing code |
| 🔍 **Fuzzy Search** | Intelligent fuzzy matching across all text fields |
| 📦 **Export/Import** | JSON and CSV export, JSON import with duplicate detection |
| 💾 **Backup/Restore** | One-command database backup and restore |

---

## Installation

AsteriaCLI can be installed system‑wide or in an isolated environment using **pipx**.

### Prerequisites

- Python **3.9** or higher
- pipx (install via `pip install --user pipx` and ensure `pipx ensurepath` is run)

### Install from the official GitHub repository

```bash
pipx install git+https://github.com/indrajit912/AsteriaCLI.git
```

### Upgrade an existing installation

```bash
pipx upgrade asteria
```

### Uninstall the application

```bash
pipx uninstall asteria
```

### Verify the installation

```bash
asteria version
```

You should see the version information printed, confirming the CLI is available on your PATH.

---

## Quick Start

```bash
# 1. Initialise the database and config
asteria init

# 2. Verify installation
asteria version

# 3. Add your first Agy conversation
asteria agy add --title "Python CLI Guide" \
               --conv-id "abc-123-def" \
               --category "Coding" \
               --tags "python,cli"

# 4. List all conversations
asteria agy list

# 5. Search conversations
asteria agy search "python"

# 6. Register a Gemini workspace
asteria gemini workspace add --path ~/projects/ai-workspace --name "AI Workspace"

# 7. Create a project
asteria gemini project create my-paper --workspace "AI Workspace"

# 8. Create and edit a prompt
asteria gemini prompt new introduction.txt --project my-paper

# 9. Run the prompt
asteria gemini prompt run introduction.txt
```

---

## Configuration

The configuration file is located at `~/.asteria/config.toml`.

### View Configuration

```bash
asteria config show
```

### Set a Value

```bash
# Change default editor
asteria config set general.default_editor code

# Set Gemini API key (prompts interactively and confirms)
asteria config set gemini.api_key

# Set default workspace
asteria config set gemini.default_workspace /path/to/workspace
```

### Configuration Options

```toml
[general]
default_editor = "vim"        # vim | nano | code | notepad++ | notepad
log_level = "INFO"            # DEBUG | INFO | WARNING | ERROR
page_size = 20                # Records per page in listings
date_format = "%Y-%m-%d %H:%M"

[gemini]
api_key = ""                  # Your Gemini API key
default_model = "gemini-2.0-flash"
default_workspace = ""        # Path to default workspace
temperature = 0.7
max_output_tokens = 8192

[agy]
default_category = "General"  # Default conversation category

[ui]
color_primary = "cyan"
color_success = "green"
color_error = "red"
show_timestamps = true
show_ids = false

[database]
backup_count = 5
auto_backup = false
```

---

## Command Reference

### Global Commands

| Command | Description |
|---------|-------------|
| `asteria init` | Initialise database and config |
| `asteria version` | Show version info |
| `asteria config show` | Show current configuration |
| `asteria config set KEY VALUE` | Set a configuration value |
| `asteria config path` | Show config file path |
| `asteria db stats` | Show database statistics |
| `asteria db backup` | Backup the database |
| `asteria db restore FILE` | Restore from a backup |

### Agy Commands

| Command | Description |
|---------|-------------|
| `asteria agy add` | Add a conversation (interactive prompts) |
| `asteria agy add --title "T" --conv-id "ID"` | Add with flags |
| `asteria agy list` | List all conversations |
| `asteria agy list --category Coding` | Filter by category |
| `asteria agy list --sort-by title --asc` | Sort ascending by title |
| `asteria agy list --page 2` | Paginate results |
| `asteria agy show <ID>` | Show full details |
| `asteria agy edit <ID> --title "New"` | Edit fields |
| `asteria agy delete <ID>` | Delete with confirmation |
| `asteria agy delete <ID> --yes` | Delete without confirmation |
| `asteria agy search "query"` | Search (fuzzy by default) |
| `asteria agy search "query" --no-fuzzy` | Exact search |
| `asteria agy export` | Export to JSON |
| `asteria agy export --format csv --output out.csv` | Export to CSV |
| `asteria agy import file.json` | Import from JSON |
| `asteria agy import file.csv` | Import from CSV |
| `asteria agy stats` | Show conversation statistics |

### Gemini Commands

#### Workspace

| Command | Description |
|---------|-------------|
| `asteria gemini workspace add --path /path --name NAME` | Register a workspace |
| `asteria gemini workspace list` | List workspaces |
| `asteria gemini workspace delete <ID>` | Delete a workspace |

#### Project

| Command | Description |
|---------|-------------|
| `asteria gemini project create NAME` | Create project (dirs auto-created) |
| `asteria gemini project list` | List all projects |
| `asteria gemini project list --workspace NAME` | Filter by workspace |
| `asteria gemini project delete NAME` | Delete a project |

#### Prompt

| Command | Description |
|---------|-------------|
| `asteria gemini prompt new NAME` | Create prompt and open editor |
| `asteria gemini prompt new NAME --no-edit` | Create without opening editor |
| `asteria gemini prompt list` | List all prompts |
| `asteria gemini prompt list --project NAME` | Filter by project |
| `asteria gemini prompt edit NAME` | Open prompt in editor |
| `asteria gemini prompt edit NAME --editor code` | Open in VS Code |
| `asteria gemini prompt delete NAME` | Delete prompt record |
| `asteria gemini prompt delete NAME --remove-file` | Delete record + file |
| `asteria gemini prompt run NAME` | Run prompt via Gemini API |
| `asteria gemini prompt run NAME --model gemini-2.0-pro` | Use specific model |

#### Output

| Command | Description |
|---------|-------------|
| `asteria gemini output list` | List all outputs |
| `asteria gemini output list --prompt NAME` | Filter by prompt |
| `asteria gemini output edit <ID>` | Edit output in editor |
| `asteria gemini output delete <ID>` | Delete output record |
| `asteria gemini output delete <ID> --remove-file` | Delete record + file |

#### Statistics

| Command | Description |
|---------|-------------|
| `asteria gemini stats` | Show Gemini module statistics |

---

## Project Structure

```
AsteriaCLI/
├── asteria/                     # Main package
│   ├── __init__.py              # Version re-exports
│   ├── cli.py                   # Main Typer entry point
│   ├── constants.py             # Global constants
│   ├── exceptions.py            # Custom exception hierarchy
│   ├── logging_config.py        # Logging setup (Rich + file)
│   ├── version.py               # Version metadata
│   ├── config/                  # Configuration management
│   │   ├── __init__.py
│   │   └── manager.py           # TOML-backed ConfigManager
│   ├── database/                # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py        # Engine, session, init_db
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── base.py          # Base, UUIDMixin, TimestampMixin
│   │       ├── agy.py           # AgyConversation model
│   │       └── gemini.py        # Workspace, Project, Prompt, Output
│   ├── modules/                 # Feature modules (plugin-like)
│   │   ├── agy/
│   │   │   ├── commands.py      # Typer CLI commands
│   │   │   ├── repository.py    # Data access layer
│   │   │   └── service.py       # Business logic
│   │   └── gemini/
│   │       ├── commands.py      # Typer CLI commands
│   │       ├── repository.py    # Data access layer
│   │       ├── runner.py        # Gemini API runner (swappable)
│   │       └── service.py       # Business logic
│   └── utils/                   # Shared utilities
│       ├── console.py           # Rich console helpers
│       ├── editor.py            # Editor launch utilities
│       ├── formatting.py        # Date, tag, CSV, JSON formatting
│       └── fuzzy.py             # Fuzzy search utilities
├── tests/                       # Test suite
│   ├── conftest.py              # Fixtures (in-memory DB, CLI runner)
│   ├── test_agy/
│   │   └── test_repository.py
│   ├── test_gemini/
│   │   └── test_repository.py
│   └── test_utils.py
├── setup.py                     # Legacy setup script
├── pyproject.toml               # PEP 517/518 build config
├── requirements.txt             # All dependencies
├── README.md
└── LICENSE
```

---

## Database Schema

```
agy_conversations
├── id             (UUID PK)
├── title          (TEXT, indexed)
├── description    (TEXT)
├── category       (TEXT, indexed)
├── conversation_id (TEXT, UNIQUE, indexed)
├── tags           (TEXT, JSON-encoded list)
├── notes          (TEXT)
├── created_at     (DATETIME)
└── updated_at     (DATETIME)

gemini_workspaces
├── id          (UUID PK)
├── path        (TEXT, UNIQUE, indexed)
├── name        (TEXT, indexed)
├── description (TEXT)
├── created_at  (DATETIME)
└── updated_at  (DATETIME)

gemini_projects
├── id           (UUID PK)
├── name         (TEXT, indexed)
├── description  (TEXT)
├── workspace_id (FK → gemini_workspaces.id CASCADE)
├── created_at   (DATETIME)
└── updated_at   (DATETIME)

gemini_prompts
├── id         (UUID PK)
├── filename   (TEXT, indexed)
├── filepath   (TEXT)
├── project_id (FK → gemini_projects.id CASCADE)
├── tags       (TEXT, JSON-encoded list)
├── notes      (TEXT)
├── created_at (DATETIME)
└── updated_at (DATETIME)

gemini_outputs
├── id         (UUID PK)
├── filename   (TEXT, indexed)
├── filepath   (TEXT)
├── prompt_id  (FK → gemini_prompts.id CASCADE)
├── created_at (DATETIME)
└── updated_at (DATETIME)
```

---

## Extending with New Modules

The architecture is designed for zero-friction extension.

To add a new provider (e.g., Claude):

```bash
# 1. Create the module directory
mkdir -p asteria/modules/claude

# 2. Add required files
touch asteria/modules/claude/__init__.py
touch asteria/modules/claude/commands.py   # Typer app
touch asteria/modules/claude/repository.py # Data access
touch asteria/modules/claude/service.py    # Business logic
```

```python
# 3. Register in asteria/cli.py (one line)
from asteria.modules.claude.commands import app as claude_app
app.add_typer(claude_app, name="claude")
```

That's it. All existing modules remain untouched.

---

## Development Guide

### Setup

```bash
git clone https://github.com/indrajit912/AsteriaCLI.git
cd AsteriaCLI
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=asteria --cov-report=html

# Specific module
pytest tests/test_agy/ -v
```

### Code Style

```bash
# Format
black asteria/ tests/

# Sort imports
isort asteria/ tests/

# Lint
flake8 asteria/ tests/

# Type check
mypy asteria/
```

### Application Data

All application data is stored in `~/.asteria/`:

```
~/.asteria/
├── asteria.db       # SQLite database
├── config.toml      # Configuration
├── asteria.log      # Application log
└── backups/         # Database backups
```

---

## Contribution Guide

1. Fork the repository on GitHub
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Write tests for new functionality
4. Ensure all tests pass: `pytest`
5. Format your code: `black asteria/ && isort asteria/`
6. Commit: `git commit -m 'Add amazing feature'`
7. Push: `git push origin feature/amazing-feature`
8. Open a Pull Request

---

## License

Copyright © 2026–Present Indrajit Ghosh. All Rights Reserved.

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
