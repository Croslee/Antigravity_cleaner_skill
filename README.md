# Antigravity Storage Cleaner

A lightweight storage management tool and Antigravity skill designed to analyze local storage consumption, reclaim orphaned conversation databases, prune intermediate step logs, and defragment SQLite databases.

![Antigravity Storage Cleaner](https://img.shields.io/badge/Antigravity-Plugin%20%26%20Skill-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Bilingual](https://img.shields.io/badge/Language-English%20%7C%20Ti%E1%BA%BFng%20Vi%E1%BB%87t-emerald)

---

## The Problem

During active coding sessions, Google Antigravity creates checkpoints, SQLite databases, and per-step execution logs:
- **Orphaned Snapshot Clones**: Every time a complex task or subagent is triggered, Antigravity creates a full copy of the conversation database (often 200MB - 350MB each). When the task finishes, Antigravity unlinks the session from the UI, but **leaves the physical `.db` file behind**.
- **Inline Side Questions**: Quick questions asked in editor tooltips create temporary database branches that remain on disk indefinitely.
- **Micro Step Logs**: A single active session can generate over 25,000 tiny JSON files in `.system_generated/steps/` and massive `transcript_full.jsonl` files.
- **Application Caches**: Chromium/Electron caches (`GPUCache`, `Code Cache`) accumulate over time.

It is common for Antigravity to silently consume **10 GB to 20 GB+** of disk space without the user knowing which files are safe to delete and which are vital.

---

## Key Features

- **Safe One-Click Cleanup**: Reclaims orphaned databases, stale locks, and application caches.
- **Recycle Bin Protection**: Integrated with the native Windows Win32 `SHFileOperationW` API. Files are moved to the Windows Recycle Bin by default rather than permanently deleted, enabling full recovery if needed.
- **Contextual Purpose Identification**: Inspects binary protobuf steps and parent references to identify why an orphaned file was created (e.g., whether it was an inline side question, a snapshot clone of a specific parent session, or a deleted conversation).
- **Conversation Slimmer**: Deletes intermediate `.steps` JSON files and temporary scratch dumps from active conversations while preserving the complete chat history in the Antigravity UI.
- **SQLite Database VACUUM**: Defragments and compacts `conversation_summaries.db` to reclaim physical disk space from empty pages.
- **Minimalist Web Dashboard**: A Zinc dark-themed interface built with the standard library and Tailwind CSS.
- **Bilingual Interface**: Toggle between English and Vietnamese at any time.
- **Zero Third-Party Dependencies**: Written entirely in pure Python standard library (`sqlite3`, `http.server`, `ctypes`, `json`, `urllib`).

---

## Installation & Setup

Clone this repository into your global Antigravity plugins directory:

```bash
git clone https://github.com/Croslee/Antigravity_cleaner_skill.git ~/.gemini/config/plugins/antigravity-storage-cleaner
```

On Windows (PowerShell):

```powershell
git clone https://github.com/Croslee/Antigravity_cleaner_skill.git "$env:USERPROFILE\.gemini\config\plugins\antigravity-storage-cleaner"
```

Once placed in the plugins folder, Antigravity discovers the skill automatically.

---

## Usage Guide

### Method 1: Antigravity Skill

In any Antigravity conversation, run the slash command:

```text
/clean
```

Or ask the assistant in natural language:

> "Check my Antigravity storage and clean up safe trash."

The agent invokes the scanner, summarizes reclaimable storage, and offers quick clean options directly in the chat.

---

### Method 2: Web Dashboard

The web dashboard provides an interactive overview of storage distribution, categorized cleanup options, and conversation management.

Launch via batch script:

```text
cleaner.bat
```

Or launch via Python:

```bash
python cleaner_server.py
```

The dashboard will open automatically in your browser at:

```text
http://localhost:9922
```

#### Dashboard Sections:
- **Safe Cleanup**: Displays orphaned database files with their file size, last modified timestamp, and original recorded context. Includes a one-click button to clean all safe items.
- **Conversations**: Lists all registered conversations with true titles, step counts, database sizes, and brain folder sizes. Supports searching, age filtering, selective deletion, and step slimming.
- **Deep Maintenance**: Provides statistics on micro step files and includes a button to run SQLite VACUUM.

---

### Method 3: Command-Line Interface (CLI)

The CLI can be used for automation, scheduled tasks, or headless environments:

```bash
# Scan and display storage summary in English (default)
python cleaner_cli.py --scan

# Scan and display summary in Vietnamese
python cleaner_cli.py --scan --lang vi

# Output scan results in raw JSON format
python cleaner_cli.py --scan --json

# Dry-run: preview files to be deleted without modifying disk
python cleaner_cli.py --clean --safe-only --dry-run

# Clean all safe trash (moves files to Recycle Bin)
python cleaner_cli.py --clean --safe-only

# Clean all safe trash permanently (bypasses Recycle Bin)
python cleaner_cli.py --clean --safe-only --permanent

# Slim down intermediate steps for a specific conversation
python cleaner_cli.py --slim-convo <CONVERSATION_ID>

# Completely delete a specific conversation by ID
python cleaner_cli.py --delete-convo <CONVERSATION_ID>

# Run SQLite VACUUM defragmentation
python cleaner_cli.py --vacuum

# Launch the Web Dashboard server
python cleaner_cli.py --web --port 9922
```

---

## Safety Architecture

1. **Path Boundary Guard**: All deletion operations are validated against strict directory boundaries (`conversations/`, `brain/`, `annotations/`, `presence/`, `crashes/`, `daemon/`, `Cache/`).
2. **Critical File Blacklist**: Essential files (`conversation_summaries.db`, `antigravity_state.pbtxt`, `installation_id`, `agyhub_summaries_proto.pb`) are permanently protected and cannot be deleted by any routine.
3. **Active Session Protection**: Active session lock files (`presence/*.lock`) and the currently running conversation are detected dynamically and excluded from cleanup candidates.
4. **Native Win32 Recycle Bin**: Uses `ctypes.windll.shell32.SHFileOperationW` with `FOF_ALLOWUNDO`. Files sent to the Recycle Bin can be restored at any time.

---

## Project Structure

```text
antigravity-storage-cleaner/
|-- plugin.json                 # Antigravity plugin manifest
|-- cleaner_core.py             # Core scanner, purpose resolver, and safety executor
|-- cleaner_server.py           # Multi-threaded HTTP REST API server
|-- cleaner_cli.py              # Command-line interface
|-- cleaner.bat                 # Windows standalone launcher script
|-- skills/
|   `-- antigravity-cleaner/
|       `-- SKILL.md            # Antigravity skill manifest with /clean slash command
|-- web/
|   `-- index.html              # Minimalist single-page dashboard UI (Zinc dark theme)
|-- .gitignore                  # Git ignore definitions
|-- LICENSE                     # MIT License
`-- README.md                   # Documentation
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
