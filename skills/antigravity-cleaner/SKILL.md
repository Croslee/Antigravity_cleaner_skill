---
name: antigravity-cleaner
description: Analyze disk storage usage in Antigravity, clean up orphaned conversations, prune cache/steps files, and launch the visual web dashboard. Trigger with /clean or when the user asks about disk space, cleaning Antigravity data, or managing conversations.
---

# Antigravity Storage Cleaner & Data Manager

This skill helps users analyze and clean up Antigravity storage data, reclaim gigabytes of orphaned conversation SQLite databases, prune micro step files, and manage historical conversation sessions.

## Quick Actions

### 1. Storage Scan (Kiểm tra dung lượng)
To scan and report current storage usage, execute:
```powershell
python "C:\Users\nateQ\.gemini\config\plugins\antigravity-storage-cleaner\cleaner_cli.py" --scan
```
Present the summary to the user in a clean table showing:
- Total Antigravity Storage
- Safe Reclaimable Space (Orphaned DBs, Caches, Stale Locks)
- Active Conversations Count
- Intermediate Step Files (count and size)

### 2. Launch Visual Web Dashboard (Mở giao diện Web)
To launch the interactive visual dashboard:
```powershell
python "C:\Users\nateQ\.gemini\config\plugins\antigravity-storage-cleaner\cleaner_cli.py" --web
```
Provide the clickable local link to the user: [Open Cleaner Dashboard](http://localhost:9922).

### 3. Safe Quick Clean (Dọn rác an toàn)
To execute the safe cleanup of orphaned files and caches:
```powershell
# Dry run first to preview:
python "C:\Users\nateQ\.gemini\config\plugins\antigravity-storage-cleaner\cleaner_cli.py" --clean --safe-only --dry-run

# Real cleanup (sends files safely to Windows Recycle Bin):
python "C:\Users\nateQ\.gemini\config\plugins\antigravity-storage-cleaner\cleaner_cli.py" --clean --safe-only
```

### 4. Database Optimization (VACUUM)
```powershell
python "C:\Users\nateQ\.gemini\config\plugins\antigravity-storage-cleaner\cleaner_cli.py" --vacuum
```
