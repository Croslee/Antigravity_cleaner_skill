"""
Antigravity Storage Cleaner - Core Engine (v2.0)
High-precision scanner, contextual purpose analyzer, safety guards,
and deletion/slimming executor with Windows Recycle Bin support.
"""

import os
import sys
import glob
import time
import json
import re
import shutil
import sqlite3
import ctypes
from datetime import datetime, timezone
from ctypes import wintypes
from typing import Dict, List, Any, Optional, Tuple, Set

# -----------------------------------------------------------------------------
# Windows Recycle Bin Support (Native Win32 API, zero external dependencies)
# -----------------------------------------------------------------------------

class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ('hwnd', wintypes.HWND),
        ('wFunc', wintypes.UINT),
        ('pFrom', wintypes.LPCWSTR),
        ('pTo', wintypes.LPCWSTR),
        ('fFlags', wintypes.WORD),
        ('fAnyOperationsAborted', wintypes.BOOL),
        ('hNameMappings', wintypes.LPVOID),
        ('lpszProgressTitle', wintypes.LPCWSTR)
    ]

FO_DELETE = 3
FOF_ALLOWUNDO = 0x0040
FOF_NOCONFIRMATION = 0x0010
FOF_SILENT = 0x0004
FOF_NOERRORUI = 0x0400

def send_to_recycle_bin(path: str) -> bool:
    """Sends a file or directory to the Windows Recycle Bin."""
    if not os.path.exists(path):
        return True
    try:
        abs_path = os.path.abspath(path) + '\0\0'
        fileop = SHFILEOPSTRUCTW()
        fileop.wFunc = FO_DELETE
        fileop.pFrom = abs_path
        fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
        res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(fileop))
        return res == 0 and not fileop.fAnyOperationsAborted
    except Exception as e:
        print(f"[RecycleBin] Error sending {path} to recycle bin: {e}", file=sys.stderr)
        return False

def delete_path(path: str, use_recycle_bin: bool = True) -> Tuple[bool, str]:
    """Safely deletes a file or directory via Recycle Bin or permanent deletion."""
    if not os.path.exists(path):
        return True, "Path does not exist"
    
    if use_recycle_bin:
        success = send_to_recycle_bin(path)
        if success:
            return True, "Moved to Recycle Bin"
        return False, "Failed to send to Recycle Bin"
    else:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=False)
            else:
                os.remove(path)
            return True, "Permanently deleted"
        except Exception as e:
            return False, str(e)


# -----------------------------------------------------------------------------
# File & Directory Helper Functions
# -----------------------------------------------------------------------------

def get_dir_size_and_count(path: str) -> Tuple[int, int]:
    """Recursively computes total bytes and file count for a directory."""
    if not os.path.exists(path):
        return 0, 0
    total_size = 0
    total_count = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total_size += entry.stat().st_size
                    total_count += 1
                elif entry.is_dir(follow_symlinks=False):
                    s, c = get_dir_size_and_count(entry.path)
                    total_size += s
                    total_count += c
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
    return total_size, total_count

def format_size(bytes_val: int) -> str:
    """Formats bytes into human-readable format."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


# -----------------------------------------------------------------------------
# Antigravity Storage Scanner
# -----------------------------------------------------------------------------

class AntigravityScanner:
    def __init__(self, antigravity_dir: Optional[str] = None):
        self.antigravity_dir = os.path.abspath(antigravity_dir or os.path.expanduser(r"~\.gemini\antigravity"))
        self.conversations_dir = os.path.join(self.antigravity_dir, "conversations")
        self.brain_dir = os.path.join(self.antigravity_dir, "brain")
        self.annotations_dir = os.path.join(self.antigravity_dir, "annotations")
        self.presence_dir = os.path.join(self.antigravity_dir, "presence")
        self.crashes_dir = os.path.join(self.antigravity_dir, "crashes")
        self.daemon_dir = os.path.join(self.antigravity_dir, "daemon")
        self.summaries_db = os.path.join(self.antigravity_dir, "conversation_summaries.db")
        self.roaming_antigravity = os.path.abspath(os.path.expandvars(r"%APPDATA%\Antigravity"))

        # Strictly protected paths that must NEVER be deleted
        self.blacklisted_files = {
            os.path.normcase(os.path.abspath(self.summaries_db)),
            os.path.normcase(os.path.abspath(self.summaries_db + "-shm")),
            os.path.normcase(os.path.abspath(self.summaries_db + "-wal")),
            os.path.normcase(os.path.abspath(os.path.join(self.antigravity_dir, "antigravity_state.pbtxt"))),
            os.path.normcase(os.path.abspath(os.path.join(self.antigravity_dir, "installation_id"))),
            os.path.normcase(os.path.abspath(os.path.join(self.antigravity_dir, "agyhub_summaries_proto.pb")))
        }

    def is_safe_path_to_clean(self, target_path: str) -> bool:
        """Enforces path boundary guards: target must reside within designated Antigravity data dirs."""
        norm_target = os.path.normcase(os.path.abspath(target_path))
        if norm_target in self.blacklisted_files:
            return False

        allowed_roots = [
            os.path.normcase(self.conversations_dir),
            os.path.normcase(self.brain_dir),
            os.path.normcase(self.annotations_dir),
            os.path.normcase(self.presence_dir),
            os.path.normcase(self.crashes_dir),
            os.path.normcase(self.daemon_dir),
            os.path.normcase(os.path.join(self.roaming_antigravity, "Cache")),
            os.path.normcase(os.path.join(self.roaming_antigravity, "GPUCache")),
            os.path.normcase(os.path.join(self.roaming_antigravity, "Code Cache")),
            os.path.normcase(os.path.join(self.roaming_antigravity, "DawnGraphiteCache")),
            os.path.normcase(os.path.join(self.roaming_antigravity, "DawnWebGPUCache")),
            os.path.normcase(os.path.join(self.roaming_antigravity, "Crashpad"))
        ]

        return any(norm_target.startswith(root + os.sep) or norm_target == root for root in allowed_roots)

    def get_known_conversations(self) -> Dict[str, Dict[str, Any]]:
        """Reads conversation_summaries.db and cross-checks with FTS index to recover missing titles."""
        convos = {}
        if not os.path.exists(self.summaries_db):
            return convos

        fts_titles = {}
        try:
            conn = sqlite3.connect(f"file:{self.summaries_db}?mode=ro", uri=True, timeout=5.0)
            cur = conn.cursor()

            try:
                cur.execute("SELECT conversation_id, title FROM conversations_fts WHERE title IS NOT NULL AND title != ''")
                for cid, t in cur.fetchall():
                    if t and t.strip():
                        fts_titles[cid] = t.strip()
            except Exception:
                pass

            cur.execute("""
                SELECT conversation_id, title, preview, step_count, last_modified_time,
                       workspace_uris, status, nesting_depth, parent_conversation_id
                FROM conversation_summaries
            """)
            for row in cur.fetchall():
                cid, title, preview, steps, mtime, ws, status, depth, parent_id = row
                resolved_title = title.strip() if title and title.strip() else fts_titles.get(cid, "")
                
                # If still empty, attempt to read first prompt from transcript
                if not resolved_title:
                    transcript_path = os.path.join(self.brain_dir, cid, ".system_generated", "logs", "transcript.jsonl")
                    if os.path.exists(transcript_path):
                        try:
                            with open(transcript_path, "r", encoding="utf-8", errors="ignore") as tf:
                                for line in tf:
                                    d = json.loads(line)
                                    if d.get("type") == "USER_INPUT":
                                        c = d.get("content", "")
                                        if "<USER_REQUEST>" in c:
                                            s = c.find("<USER_REQUEST>") + 14
                                            e = c.find("</USER_REQUEST>", s)
                                            resolved_title = c[s:e].strip() if e != -1 else c[s:s+80].strip()
                                        else:
                                            resolved_title = c.strip()[:80]
                                        break
                        except Exception:
                            pass

                convos[cid] = {
                    "conversation_id": cid,
                    "title": resolved_title or "Untitled Conversation",
                    "preview": preview or "",
                    "step_count": steps or 0,
                    "last_modified_time": mtime or "",
                    "workspace_uris": ws or "",
                    "status": status or "",
                    "nesting_depth": depth or 0,
                    "parent_conversation_id": parent_id or ""
                }
            conn.close()
        except Exception as e:
            print(f"[Scanner] Error reading conversation_summaries.db: {e}", file=sys.stderr)
        return convos

    def inspect_db_purpose(self, cid: str, db_path: str, known_convos: dict) -> dict:
        """
        Deeply inspects an orphaned SQLite DB to identify its original purpose,
        prompt snippet, role, parent relationship, and file health status.
        Returns bilingual contextual descriptions.
        """
        size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        # Handle 0-byte ghost files
        if size == 0:
            return {
                "category_vi": "File rác 0-byte (Ghost file)",
                "category_en": "0-Byte Ghost File",
                "topic_vi": "Tập tin rỗng do tiến trình tắt đột ngột để lại",
                "topic_en": "Empty stale file left behind by terminated process",
                "parent_id": None,
                "parent_title": None,
                "step_count": 0,
                "is_ghost": True
            }

        parent_id = None
        topic = None
        category_vi = "Phiên cũ đã xoá"
        category_en = "Deleted Conversation"
        step_count = 0

        # 1. Inspect SQLite parent_references & steps
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
            cur = conn.cursor()

            try:
                cur.execute("SELECT count(*) FROM steps")
                step_count = cur.fetchone()[0]
            except Exception:
                step_count = 0

            try:
                cur.execute("SELECT data FROM parent_references LIMIT 1")
                row = cur.fetchone()
                if row and row[0]:
                    p_text = row[0].decode("utf-8", errors="ignore")
                    uuids = re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", p_text)
                    if uuids:
                        parent_id = uuids[-1]
            except Exception:
                pass

            # Scan steps for Role or USER_REQUEST
            try:
                cur.execute("SELECT step_payload FROM steps WHERE step_payload IS NOT NULL LIMIT 40")
                for srow in cur.fetchall():
                    raw_text = srow[0].decode("utf-8", errors="ignore")
                    if "<USER_REQUEST>" in raw_text and not topic:
                        s = raw_text.find("<USER_REQUEST>") + 14
                        e = raw_text.find("</USER_REQUEST>", s)
                        topic = raw_text[s:e].strip() if e != -1 else raw_text[s:s+140].strip()
                        break
                    elif 'Role' in raw_text and not topic:
                        m = re.search(r'\"Role\":\s*\"([^\"]+)\"', raw_text)
                        if m:
                            role = m.group(1)
                            category_vi = "Subagent phân nhánh"
                            category_en = "Branched Subagent"
                            topic = f"Tác vụ Subagent: {role}"
                            break
            except Exception:
                pass

            conn.close()
        except Exception:
            pass

        # 2. Check parent title
        parent_info = known_convos.get(parent_id)
        parent_title = parent_info.get("title") if parent_info else None

        if parent_title:
            category_vi = "Nhánh bản sao (Snapshot)"
            category_en = "Snapshot Branch"
            topic_vi = f"Bản sao lưu nhánh của phiên: '{parent_title}'"
            topic_en = f"Trajectory snapshot of session: '{parent_title}'"
        elif parent_id:
            category_vi = "Nhánh của phiên cũ"
            category_en = "Branch of Deleted Session"
            topic_vi = f"Nhánh sao lưu của phiên cũ đã xoá ({parent_id[:8]}...)"
            topic_en = f"Snapshot branch of deleted session ({parent_id[:8]}...)"
        else:
            # 3. Check brain transcript for exact user request
            if not topic:
                transcript_path = os.path.join(self.brain_dir, cid, ".system_generated", "logs", "transcript.jsonl")
                if os.path.exists(transcript_path):
                    try:
                        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as tf:
                            for line in tf:
                                d = json.loads(line)
                                if d.get("type") == "USER_INPUT":
                                    c_text = d.get("content", "")
                                    if "<USER_REQUEST>" in c_text:
                                        s = c_text.find("<USER_REQUEST>") + 14
                                        e = c_text.find("</USER_REQUEST>", s)
                                        topic = c_text[s:e].strip() if e != -1 else c_text[s:s+140].strip()
                                    else:
                                        topic = c_text.strip()[:140]
                                    break
                    except Exception:
                        pass

            if topic and "side question" in topic.lower():
                category_vi = "Câu hỏi phụ (Side Question)"
                category_en = "Inline Side Question"
                m_sq = re.search(r'Side Question:\s*(.+)', topic, re.IGNORECASE)
                clean_topic = m_sq.group(1).strip() if m_sq else topic
                topic_vi = f"Câu hỏi phụ inline trong editor: {clean_topic[:70]}"
                topic_en = f"Inline editor side question: {clean_topic[:70]}"
            elif topic:
                topic_vi = topic.replace("\n", " ").replace("\r", " ").strip()
                topic_en = topic_vi
            else:
                topic_vi = "Bản ghi phụ / Trajectory checkpoint cũ"
                topic_en = "Stale trajectory checkpoint / orphaned log"

        topic_vi = topic_vi[:90] + ("..." if len(topic_vi) > 90 else "")
        topic_en = topic_en[:90] + ("..." if len(topic_en) > 90 else "")

        return {
            "category_vi": category_vi,
            "category_en": category_en,
            "topic_vi": topic_vi,
            "topic_en": topic_en,
            "parent_id": parent_id,
            "parent_title": parent_title,
            "step_count": step_count,
            "is_ghost": False
        }

    def detect_active_sessions(self) -> Set[str]:
        """Detects active or recently running conversations to protect them from deletion."""
        active_cids = set()

        env_cid = os.environ.get("ANTIGRAVITY_CONVERSATION_ID")
        if env_cid:
            active_cids.add(env_cid)

        if os.path.exists(self.presence_dir):
            now = time.time()
            for entry in os.scandir(self.presence_dir):
                if entry.name.endswith(".lock"):
                    cid = entry.name[:-5]
                    try:
                        mtime = entry.stat().st_mtime
                        if now - mtime < 10800:  # 3 hours
                            active_cids.add(cid)
                    except OSError:
                        pass
        return active_cids

    def scan_all(self, current_session_id: Optional[str] = None) -> Dict[str, Any]:
        """Performs a comprehensive scan of all Antigravity directories and caches."""
        active_protected = self.detect_active_sessions()
        if current_session_id:
            active_protected.add(current_session_id)

        known_convos = self.get_known_conversations()
        known_cids = set(known_convos.keys())

        # 1. Scan conversations/ directory for DB files
        orphaned_dbs = []
        active_dbs_map = {}
        total_conv_dir_bytes = 0

        if os.path.exists(self.conversations_dir):
            for entry in os.scandir(self.conversations_dir):
                if entry.is_file():
                    try:
                        size = entry.stat().st_size
                        mtime = entry.stat().st_mtime
                        total_conv_dir_bytes += size
                        if entry.name.endswith(".db"):
                            cid = entry.name[:-3]
                            item_data = {
                                "id": cid,
                                "filename": entry.name,
                                "path": entry.path,
                                "size_bytes": size,
                                "size_str": format_size(size),
                                "mtime": mtime,
                                "mtime_str": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
                                "is_protected": cid in active_protected
                            }
                            if cid not in known_cids:
                                purpose_info = self.inspect_db_purpose(cid, entry.path, known_convos)
                                item_data.update(purpose_info)
                                orphaned_dbs.append(item_data)
                            else:
                                active_dbs_map[cid] = item_data
                    except OSError:
                        continue

        orphaned_dbs.sort(key=lambda x: x["size_bytes"], reverse=True)

        # 2. Scan brain/ directory
        orphaned_brain_folders = []
        active_brain_map = {}
        total_brain_bytes = 0

        deep_steps_count = 0
        deep_steps_bytes = 0
        deep_logs_count = 0
        deep_logs_bytes = 0
        deep_scratch_count = 0
        deep_scratch_bytes = 0
        deep_tempmedia_bytes = 0

        if os.path.exists(self.brain_dir):
            for entry in os.scandir(self.brain_dir):
                if entry.is_dir():
                    cid = entry.name
                    folder_path = entry.path

                    steps_path = os.path.join(folder_path, ".system_generated", "steps")
                    logs_path = os.path.join(folder_path, ".system_generated", "logs")
                    scratch_path = os.path.join(folder_path, "scratch")
                    tempmedia_path = os.path.join(folder_path, ".tempmediaStorage")

                    s_sz, s_cnt = get_dir_size_and_count(steps_path)
                    l_sz, l_cnt = get_dir_size_and_count(logs_path)
                    sc_sz, sc_cnt = get_dir_size_and_count(scratch_path)
                    tm_sz, tm_cnt = get_dir_size_and_count(tempmedia_path)

                    total_folder_size, total_folder_cnt = get_dir_size_and_count(folder_path)
                    total_brain_bytes += total_folder_size

                    deep_steps_count += s_cnt
                    deep_steps_bytes += s_sz
                    deep_logs_count += l_cnt
                    deep_logs_bytes += l_sz
                    deep_scratch_count += sc_cnt
                    deep_scratch_bytes += sc_sz
                    deep_tempmedia_bytes += tm_sz

                    item_data = {
                        "id": cid,
                        "path": folder_path,
                        "total_bytes": total_folder_size,
                        "total_str": format_size(total_folder_size),
                        "file_count": total_folder_cnt,
                        "steps_bytes": s_sz,
                        "steps_count": s_cnt,
                        "logs_bytes": l_sz,
                        "logs_count": l_cnt,
                        "scratch_bytes": sc_sz,
                        "scratch_count": sc_cnt,
                        "tempmedia_bytes": tm_sz,
                        "is_protected": cid in active_protected
                    }

                    if cid not in known_cids:
                        orphaned_brain_folders.append(item_data)
                    else:
                        active_brain_map[cid] = item_data

        orphaned_brain_folders.sort(key=lambda x: x["total_bytes"], reverse=True)

        # 3. Build Active Conversations List
        active_conversations = []
        for cid, info in known_convos.items():
            db_item = active_dbs_map.get(cid, {})
            brain_item = active_brain_map.get(cid, {})

            db_size = db_item.get("size_bytes", 0)
            brain_size = brain_item.get("total_bytes", 0)
            total_size = db_size + brain_size

            mtime_str = info.get("last_modified_time", "")
            mtime_clean = mtime_str[:16].replace("T", " ") if mtime_str else "Unknown"

            active_conversations.append({
                "conversation_id": cid,
                "title": info["title"],
                "preview": info["preview"][:120] + "..." if len(info.get("preview", "")) > 120 else info.get("preview", ""),
                "step_count": info["step_count"],
                "last_modified": mtime_clean,
                "workspace": os.path.basename(info.get("workspace_uris", "").rstrip("/\\")) or "No workspace",
                "db_bytes": db_size,
                "db_str": format_size(db_size),
                "brain_bytes": brain_size,
                "brain_str": format_size(brain_size),
                "total_bytes": total_size,
                "total_str": format_size(total_size),
                "steps_bytes": brain_item.get("steps_bytes", 0),
                "logs_bytes": brain_item.get("logs_bytes", 0),
                "scratch_bytes": brain_item.get("scratch_bytes", 0),
                "can_slim": (brain_item.get("steps_bytes", 0) + brain_item.get("scratch_bytes", 0)) > 500000,
                "is_protected": cid in active_protected,
                "has_db": bool(db_item),
                "has_brain": bool(brain_item)
            })

        active_conversations.sort(key=lambda x: x["total_bytes"], reverse=True)

        # 4. Scan App Caches
        app_caches = []
        total_cache_bytes = 0
        cache_folders = [
            ("Browser Cache", "Browser Cache", "Cache", "Chromium HTTP cache files", "Tập tin bộ đệm web HTTP"),
            ("GPU Cache", "GPU Cache", "GPUCache", "Graphics pipeline shader & texture cache", "Bộ đệm đồ họa shader & texture"),
            ("Code Cache", "Code Cache", "Code Cache", "Compiled JavaScript V8 bytecodes", "Mã JavaScript V8 biên dịch sẵn"),
            ("Dawn WebGPU Cache", "Dawn WebGPU Cache", "DawnWebGPUCache", "WebGPU pipeline caches", "Bộ đệm WebGPU"),
            ("Dawn Graphite Cache", "Dawn Graphite Cache", "DawnGraphiteCache", "Skia Graphite graphics cache", "Bộ đệm đồ họa Skia"),
            ("Crashpad Dumps", "Crashpad Dumps", "Crashpad", "Crashpad minidumps", "Nhật ký sự cố Crashpad")
        ]

        if os.path.exists(self.roaming_antigravity):
            for name_en, name_vi, folder_name, desc_en, desc_vi in cache_folders:
                cpath = os.path.join(self.roaming_antigravity, folder_name)
                if os.path.exists(cpath):
                    sz, cnt = get_dir_size_and_count(cpath)
                    total_cache_bytes += sz
                    if sz > 0:
                        app_caches.append({
                            "name_en": name_en,
                            "name_vi": name_vi,
                            "folder": folder_name,
                            "path": cpath,
                            "size_bytes": sz,
                            "size_str": format_size(sz),
                            "file_count": cnt,
                            "desc_en": desc_en,
                            "desc_vi": desc_vi
                        })

        # 5. Scan Stale System Files
        stale_system_files = []
        stale_system_bytes = 0

        if os.path.exists(self.presence_dir):
            for entry in os.scandir(self.presence_dir):
                if entry.name.endswith(".lock"):
                    cid = entry.name[:-5]
                    if cid not in active_protected:
                        sz = entry.stat().st_size
                        stale_system_bytes += sz
                        stale_system_files.append({
                            "type": "presence_lock",
                            "name": entry.name,
                            "path": entry.path,
                            "size_bytes": sz
                        })

        if os.path.exists(self.daemon_dir):
            for entry in os.scandir(self.daemon_dir):
                if entry.name.endswith(".json"):
                    sz = entry.stat().st_size
                    stale_system_bytes += sz
                    stale_system_files.append({
                        "type": "daemon_hub",
                        "name": entry.name,
                        "path": entry.path,
                        "size_bytes": sz
                    })

        if os.path.exists(self.crashes_dir):
            for entry in os.scandir(self.crashes_dir):
                sz = entry.stat().st_size
                stale_system_bytes += sz
                stale_system_files.append({
                    "type": "crash_log",
                    "name": entry.name,
                    "path": entry.path,
                    "size_bytes": sz
                })

        summaries_db_size = os.path.getsize(self.summaries_db) if os.path.exists(self.summaries_db) else 0
        orphaned_dbs_bytes = sum(x["size_bytes"] for x in orphaned_dbs)
        orphaned_brain_bytes = sum(x["total_bytes"] for x in orphaned_brain_folders)
        safe_reclaimable_bytes = orphaned_dbs_bytes + orphaned_brain_bytes + total_cache_bytes + stale_system_bytes
        total_managed_bytes = total_conv_dir_bytes + total_brain_bytes + total_cache_bytes + summaries_db_size

        return {
            "summary": {
                "total_managed_bytes": total_managed_bytes,
                "total_managed_str": format_size(total_managed_bytes),
                "safe_reclaimable_bytes": safe_reclaimable_bytes,
                "safe_reclaimable_str": format_size(safe_reclaimable_bytes),
                "active_conversations_count": len(active_conversations),
                "orphaned_conversations_count": len(orphaned_dbs),
                "protected_count": len(active_protected)
            },
            "safe_items": {
                "orphaned_dbs": orphaned_dbs,
                "orphaned_dbs_bytes": orphaned_dbs_bytes,
                "orphaned_dbs_str": format_size(orphaned_dbs_bytes),
                "orphaned_brain": orphaned_brain_folders,
                "orphaned_brain_bytes": orphaned_brain_bytes,
                "orphaned_brain_str": format_size(orphaned_brain_bytes),
                "app_caches": app_caches,
                "app_caches_bytes": total_cache_bytes,
                "app_caches_str": format_size(total_cache_bytes),
                "stale_system": stale_system_files,
                "stale_system_bytes": stale_system_bytes,
                "stale_system_str": format_size(stale_system_bytes)
            },
            "active_conversations": active_conversations,
            "deep_stats": {
                "steps_count": deep_steps_count,
                "steps_bytes": deep_steps_bytes,
                "steps_str": format_size(deep_steps_bytes),
                "logs_count": deep_logs_count,
                "logs_bytes": deep_logs_bytes,
                "logs_str": format_size(deep_logs_bytes),
                "scratch_count": deep_scratch_count,
                "scratch_bytes": deep_scratch_bytes,
                "scratch_str": format_size(deep_scratch_bytes),
                "tempmedia_bytes": deep_tempmedia_bytes,
                "tempmedia_str": format_size(deep_tempmedia_bytes)
            }
        }


# -----------------------------------------------------------------------------
# Antigravity Cleaner Executor
# -----------------------------------------------------------------------------

class AntigravityCleaner:
    def __init__(self, scanner: Optional[AntigravityScanner] = None):
        self.scanner = scanner or AntigravityScanner()

    def clean_safe_items(self, dry_run: bool = False, use_recycle_bin: bool = True) -> Dict[str, Any]:
        """Cleans all safe items (orphaned dbs, orphaned brain, app caches, stale system files)."""
        scan_res = self.scanner.scan_all()
        safe_items = scan_res["safe_items"]

        deleted_paths = []
        freed_bytes = 0
        errors = []

        # 1. Clean Orphaned DBs
        for db in safe_items["orphaned_dbs"]:
            if db.get("is_protected"):
                continue
            path = db["path"]
            if not self.scanner.is_safe_path_to_clean(path):
                continue
            sz = db["size_bytes"]
            if dry_run:
                deleted_paths.append(path)
                freed_bytes += sz
            else:
                ok, msg = delete_path(path, use_recycle_bin=use_recycle_bin)
                if ok:
                    deleted_paths.append(path)
                    freed_bytes += sz
                    for ext in ["-shm", "-wal"]:
                        extra = path + ext
                        if os.path.exists(extra):
                            delete_path(extra, use_recycle_bin=use_recycle_bin)
                else:
                    errors.append(f"Failed to delete {path}: {msg}")

        # 2. Clean Orphaned Brain folders
        for folder in safe_items["orphaned_brain"]:
            if folder.get("is_protected"):
                continue
            path = folder["path"]
            if not self.scanner.is_safe_path_to_clean(path):
                continue
            sz = folder["total_bytes"]
            if dry_run:
                deleted_paths.append(path)
                freed_bytes += sz
            else:
                ok, msg = delete_path(path, use_recycle_bin=use_recycle_bin)
                if ok:
                    deleted_paths.append(path)
                    freed_bytes += sz
                else:
                    errors.append(f"Failed to delete {path}: {msg}")

        # 3. Clean App Caches
        for cache in safe_items["app_caches"]:
            cpath = cache["path"]
            if not self.scanner.is_safe_path_to_clean(cpath):
                continue
            sz = cache["size_bytes"]
            if dry_run:
                deleted_paths.append(cpath)
                freed_bytes += sz
            else:
                try:
                    for entry in os.scandir(cpath):
                        delete_path(entry.path, use_recycle_bin=False)
                    deleted_paths.append(cpath)
                    freed_bytes += sz
                except Exception as e:
                    errors.append(f"Failed to clean cache {cpath}: {e}")

        # 4. Clean Stale System files
        for sf in safe_items["stale_system"]:
            path = sf["path"]
            if not self.scanner.is_safe_path_to_clean(path):
                continue
            sz = sf["size_bytes"]
            if dry_run:
                deleted_paths.append(path)
                freed_bytes += sz
            else:
                ok, msg = delete_path(path, use_recycle_bin=False)
                if ok:
                    deleted_paths.append(path)
                    freed_bytes += sz

        return {
            "success": len(errors) == 0,
            "dry_run": dry_run,
            "deleted_count": len(deleted_paths),
            "freed_bytes": freed_bytes,
            "freed_str": format_size(freed_bytes),
            "errors": errors
        }

    def delete_conversation(self, cid: str, dry_run: bool = False, use_recycle_bin: bool = True) -> Dict[str, Any]:
        """Completely removes an active conversation and unregisters it from conversation_summaries.db."""
        active_protected = self.scanner.detect_active_sessions()
        if cid in active_protected:
            return {"success": False, "error": f"Conversation {cid} is currently active or protected."}

        db_file = os.path.join(self.scanner.conversations_dir, f"{cid}.db")
        brain_folder = os.path.join(self.scanner.brain_dir, cid)
        ann_file = os.path.join(self.scanner.annotations_dir, f"{cid}.pbtxt")
        lock_file = os.path.join(self.scanner.presence_dir, f"{cid}.lock")

        freed_bytes = 0
        if os.path.exists(db_file):
            freed_bytes += os.path.getsize(db_file)
        if os.path.exists(brain_folder):
            s, _ = get_dir_size_and_count(brain_folder)
            freed_bytes += s

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "conversation_id": cid,
                "freed_bytes": freed_bytes,
                "freed_str": format_size(freed_bytes)
            }

        errors = []
        if os.path.exists(db_file) and self.scanner.is_safe_path_to_clean(db_file):
            ok, msg = delete_path(db_file, use_recycle_bin=use_recycle_bin)
            if not ok: errors.append(f"DB file: {msg}")
            for ext in ["-shm", "-wal"]:
                if os.path.exists(db_file + ext):
                    delete_path(db_file + ext, use_recycle_bin=use_recycle_bin)

        if os.path.exists(brain_folder) and self.scanner.is_safe_path_to_clean(brain_folder):
            ok, msg = delete_path(brain_folder, use_recycle_bin=use_recycle_bin)
            if not ok: errors.append(f"Brain folder: {msg}")

        if os.path.exists(ann_file) and self.scanner.is_safe_path_to_clean(ann_file):
            delete_path(ann_file, use_recycle_bin=use_recycle_bin)

        if os.path.exists(lock_file) and self.scanner.is_safe_path_to_clean(lock_file):
            delete_path(lock_file, use_recycle_bin=False)

        # Unregister from conversation_summaries.db
        if os.path.exists(self.scanner.summaries_db):
            try:
                conn = sqlite3.connect(self.scanner.summaries_db, timeout=10.0)
                cur = conn.cursor()
                cur.execute("DELETE FROM conversation_summaries WHERE conversation_id = ?", (cid,))
                try:
                    cur.execute("DELETE FROM conversations_fts WHERE conversation_id = ?", (cid,))
                except Exception:
                    pass
                conn.commit()
                conn.close()
            except Exception as e:
                errors.append(f"Failed to unregister from conversation_summaries.db: {e}")

        return {
            "success": len(errors) == 0,
            "dry_run": False,
            "conversation_id": cid,
            "freed_bytes": freed_bytes,
            "freed_str": format_size(freed_bytes),
            "errors": errors
        }

    def slim_conversation(self, cid: str, dry_run: bool = False, use_recycle_bin: bool = True) -> Dict[str, Any]:
        """Prunes heavy step JSON files and scratch dumps for a conversation while keeping its chat history intact."""
        brain_folder = os.path.join(self.scanner.brain_dir, cid)
        if not os.path.exists(brain_folder):
            return {"success": True, "freed_bytes": 0, "freed_str": "0 B"}

        steps_folder = os.path.join(brain_folder, ".system_generated", "steps")
        scratch_folder = os.path.join(brain_folder, "scratch")
        tempmedia_folder = os.path.join(brain_folder, ".tempmediaStorage")

        freed_bytes = 0
        s_sz, _ = get_dir_size_and_count(steps_folder)
        sc_sz, _ = get_dir_size_and_count(scratch_folder)
        tm_sz, _ = get_dir_size_and_count(tempmedia_folder)
        freed_bytes = s_sz + sc_sz + tm_sz

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "conversation_id": cid,
                "freed_bytes": freed_bytes,
                "freed_str": format_size(freed_bytes)
            }

        errors = []
        if os.path.exists(steps_folder) and self.scanner.is_safe_path_to_clean(steps_folder):
            ok, msg = delete_path(steps_folder, use_recycle_bin=use_recycle_bin)
            if not ok: errors.append(msg)

        if os.path.exists(scratch_folder) and self.scanner.is_safe_path_to_clean(scratch_folder):
            ok, msg = delete_path(scratch_folder, use_recycle_bin=use_recycle_bin)
            if not ok: errors.append(msg)

        if os.path.exists(tempmedia_folder) and self.scanner.is_safe_path_to_clean(tempmedia_folder):
            ok, msg = delete_path(tempmedia_folder, use_recycle_bin=use_recycle_bin)
            if not ok: errors.append(msg)

        return {
            "success": len(errors) == 0,
            "dry_run": False,
            "conversation_id": cid,
            "freed_bytes": freed_bytes,
            "freed_str": format_size(freed_bytes),
            "errors": errors
        }

    def vacuum_databases(self) -> Dict[str, Any]:
        """Runs VACUUM on conversation_summaries.db to reclaim free pages and defragment."""
        freed = 0
        if os.path.exists(self.scanner.summaries_db):
            try:
                before = os.path.getsize(self.scanner.summaries_db)
                conn = sqlite3.connect(self.scanner.summaries_db, timeout=10.0)
                conn.execute("VACUUM")
                conn.close()
                after = os.path.getsize(self.scanner.summaries_db)
                freed = max(0, before - after)
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {
            "success": True,
            "freed_bytes": freed,
            "freed_str": format_size(freed)
        }
