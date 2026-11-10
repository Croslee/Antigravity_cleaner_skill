# Antigravity Storage Cleaner & Optimizer 🚀

An intelligent, safe, and minimalist storage management tool and Antigravity Skill designed to reclaim gigabytes of orphaned databases, purge redundant intermediate step logs, and optimize Antigravity data storage.

![Antigravity Storage Cleaner](https://img.shields.io/badge/Antigravity-Plugin%20%26%20Skill-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Bilingual](https://img.shields.io/badge/Language-English%20%7C%20Ti%E1%BA%BFng%20Vi%E1%BB%87t-emerald)

---

## 🧐 The Problem

During active coding sessions, Google Antigravity creates checkpoints, SQLite databases, and per-step execution logs:
- **Orphaned Snapshot Clones**: Every time a complex task or subagent is triggered, Antigravity creates a full copy of the conversation database (often 200MB - 350MB each). When the task finishes, Antigravity unlinks the session from the UI, but **leaves the physical `.db` file behind**.
- **Inline Side Questions**: Quick questions asked in editor tooltips create temporary database branches that remain on disk indefinitely.
- **Micro Step Logs**: A single active session can generate over 25,000 tiny JSON files in `.system_generated/steps/` and massive `transcript_full.jsonl` files.
- **Application Caches**: Chromium/Electron caches (`GPUCache`, `Code Cache`) accumulate over time.

It is common for Antigravity to silently consume **10 GB to 20 GB+** of disk space without the user knowing which files are safe to delete and which are vital.

---

## ✨ Features

- **⚡ 1-Click Safe Cleanup**: Instantly reclaims gigabytes of orphaned databases, stale locks, and application caches.
- **🛡️ Windows Recycle Bin Guard**: Uses native Win32 `SHFileOperationW` API so deleted files are moved to the **Windows Recycle Bin** rather than permanently deleted. You can restore any file with 100% confidence.
- **🔍 Contextual Purpose Inspection**: Understand what each orphaned database was originally used for:
  - Trajectory snapshot clones (identifies the parent conversation title).
  - Inline side questions (extracts the exact question asked in the editor).
  - Recovered prompts from historical sessions.
  - 0-byte ghost files from ungraceful shutdowns.
- **✂️ Conversation Slimmer**: Prunes heavy `.steps` JSON files and scratch dumps from active conversations while **keeping 100% of the chat history intact** in the Antigravity UI.
- **🗜️ SQLite VACUUM Defragmentation**: Defragments and compacts `conversation_summaries.db` to reclaim free disk pages.
- **🎨 Minimalist Web Dashboard**: Clean, distraction-free Zinc dark theme inspired by modern developer tools (Linear / Vercel).
- **🌐 Bilingual Support**: Seamless one-click switching between **English** and **Tiếng Việt** (`VI | EN`).
- **🔒 Active Session Guard**: Automatically detects active conversation locks and prevents modifying the current session.

---

## 🚀 Quick Start & How to Use

### Method 1: Use as an Antigravity Skill / Plugin (Recommended)

1. Clone or copy this repository into your global Antigravity plugins directory:
   ```powershell
   git clone https://github.com/Croslee/Antigravity_cleaner_skill.git "$env:USERPROFILE\.gemini\config\plugins\antigravity-storage-cleaner"
   ```

2. Inside any Antigravity conversation, simply type:
   ```text
   /clean
   ```
   or ask the assistant:
   > *"Check my Antigravity disk storage and clean up safe trash"*

   Antigravity will scan your storage, summarize the reclaimable space, and provide options to clean safely or open the dashboard.

---

### Method 2: Standalone Web Dashboard (1-Click Launch)

You can launch the dashboard even when Antigravity is closed or unresponsive:

1. Double-click the launch script:
   ```text
   cleaner.bat
   ```
   *(or run `python cleaner_server.py` in terminal)*

2. Your browser will automatically open:
   ```text
   http://localhost:9922
   ```

3. Explore the tabs:
   - **Safe Cleanup**: Review orphaned databases, original user prompts, and click **Clean Safe Trash**.
   - **Conversations**: Search, filter by age/size, and selectively slim or delete old sessions.
   - **Deep Maintenance**: Clean intermediate step files and run SQLite VACUUM.

---

### Method 3: Command-Line Interface (CLI)

The CLI requires zero third-party dependencies (built with Python standard library):

```powershell
# Scan storage and display bilingual summary
python cleaner_cli.py --scan --lang en

# Dry-run: preview files and space to be freed without deleting
python cleaner_cli.py --clean --safe-only --dry-run --lang en

# Execute safe clean (moves files to Recycle Bin)
python cleaner_cli.py --clean --safe-only --lang en

# Permanent clean (bypasses Recycle Bin)
python cleaner_cli.py --clean --safe-only --permanent

# Slim down steps for a specific conversation
python cleaner_cli.py --slim-convo <CONVERSATION_ID>

# Delete a specific conversation completely
python cleaner_cli.py --delete-convo <CONVERSATION_ID>

# Run SQLite VACUUM
python cleaner_cli.py --vacuum
```

---

## 📁 Repository Structure

```text
Antigravity_cleaner_skill/
├── plugin.json                 # Antigravity plugin manifest
├── cleaner_core.py             # Core scanner, purpose inspector & Win32 safety executor
├── cleaner_server.py           # Multi-threaded local HTTP REST API server
├── cleaner_cli.py              # Command-line interface with EN/VI support
├── cleaner.bat                 # 1-click Windows desktop launcher
├── skills/
│   └── antigravity-cleaner/
│       └── SKILL.md            # Antigravity skill definition with /clean slash command
├── web/
│   └── index.html              # Minimalist, bilingual single-page Web Dashboard
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT License
└── README.md                   # Documentation (this file)
```

---

## 🛡️ Safety & Architecture Guarantees

1. **Path Boundary Guard**: Deletions are strictly restricted to designated cache and conversation folders. Critical databases like `conversation_summaries.db`, `antigravity_state.pbtxt`, and project workspaces are strictly blacklisted from deletion.
2. **Win32 Recycle Bin API**: Utilizes `ctypes.windll.shell32.SHFileOperationW` with `FOF_ALLOWUNDO`. No files are permanently lost unless explicitly toggled by the user.
3. **Zero Third-Party Dependencies**: Written entirely in pure Python using built-in modules (`sqlite3`, `http.server`, `ctypes`, `json`, `urllib`). No `pip install` required.

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
