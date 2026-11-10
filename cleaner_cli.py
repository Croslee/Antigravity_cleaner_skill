#!/usr/bin/env python3
"""
Antigravity Storage Cleaner - CLI Interface (v2.0)
Provides command-line scanning, cleaning, and server launcher.
Supports bilingual output (--lang en / --lang vi).
"""

import os
import sys
import json
import argparse
from cleaner_core import AntigravityScanner, AntigravityCleaner, format_size

def print_banner(lang='en'):
    print("=" * 68)
    if lang == 'vi':
        print("        Trinh Don Dep & Toi Uu Dung Luong Antigravity        ")
    else:
        print("        Antigravity Storage Cleaner & Optimizer        ")
    print("=" * 68)

def cmd_scan(args):
    lang = getattr(args, 'lang', 'en')
    print_banner(lang)
    if lang == 'en':
        print("Scanning Antigravity storage directories...")
    else:
        print("Dang quet cac thu muc luu tru cua Antigravity...")

    scanner = AntigravityScanner()
    res = scanner.scan_all(current_session_id=args.active_id)

    if args.json:
        print(json.dumps(res, indent=2))
        return

    summary = res["summary"]
    safe = res["safe_items"]
    deep = res["deep_stats"]

    if lang == 'en':
        print("\n📊 STORAGE SUMMARY:")
        print(f"  • Total Managed Storage: {summary['total_managed_str']}")
        print(f"  • 🟢 Safe Reclaimable Space: {summary['safe_reclaimable_str']} (Can be freed immediately!)")
        print(f"  • Active Conversations: {summary['active_conversations_count']}")
        print(f"  • Orphaned Databases: {summary['orphaned_conversations_count']}")
        print(f"  • Protected Active Sessions: {summary['protected_count']}")

        print("\n📁 SAFE CLEANABLE CATEGORIES:")
        print(f"  1. Orphaned Databases: {safe['orphaned_dbs_str']} ({len(safe['orphaned_dbs'])} files)")
        print(f"  2. Orphaned Brain Folders: {safe['orphaned_brain_str']} ({len(safe['orphaned_brain'])} dirs)")
        print(f"  3. Application Caches: {safe['app_caches_str']}")
        print(f"  4. Stale Locks & Daemon Hubs: {safe['stale_system_str']} ({len(safe['stale_system'])} files)")

        print("\n🧠 INTERNAL DATA & STEPS:")
        print(f"  • Intermediate Steps (.steps): {deep['steps_count']} files ({deep['steps_str']})")
        print(f"  • Detailed Logs & Transcripts: {deep['logs_count']} files ({deep['logs_str']})")
        print(f"  • Scratch & Temp Dumps: {deep['scratch_count']} files ({deep['scratch_str']})")

        print("\n💡 ACTION SHORTCUTS:")
        print("  • Clean safe trash: python cleaner_cli.py --clean --safe-only")
        print("  • Launch Minimalist Dashboard: python cleaner_cli.py --web")
    else:
        print("\n📊 TỔNG QUAN DUNG LƯỢNG:")
        print(f"  • Tổng dung lượng quản lý: {summary['total_managed_str']}")
        print(f"  • 🟢 Rác an toàn có thể thu hồi: {summary['safe_reclaimable_str']} (Có thể giải phóng ngay!)")
        print(f"  • Hội thoại đang hoạt động: {summary['active_conversations_count']}")
        print(f"  • Database mồ côi (đã xoá/rác): {summary['orphaned_conversations_count']}")
        print(f"  • Phiên đang được bảo vệ: {summary['protected_count']}")

        print("\n📁 CHI TIẾT MỤC RÁC AN TOÀN:")
        print(f"  1. Database mồ côi: {safe['orphaned_dbs_str']} ({len(safe['orphaned_dbs'])} files)")
        print(f"  2. Thư mục Brain mồ côi: {safe['orphaned_brain_str']} ({len(safe['orphaned_brain'])} dirs)")
        print(f"  3. Cache ứng dụng: {safe['app_caches_str']}")
        print(f"  4. File khoá & Hub tiến trình rác: {safe['stale_system_str']} ({len(safe['stale_system'])} files)")

        print("\n🧠 THỐNG KÊ BƯỚC CHẠY & TRANSCRIPTS:")
        print(f"  • File bước chạy trung gian (Steps): {deep['steps_count']} files ({deep['steps_str']})")
        print(f"  • Logs & Transcripts: {deep['logs_count']} files ({deep['logs_str']})")
        print(f"  • Scratch & Temp Dumps: {deep['scratch_count']} files ({deep['scratch_str']})")

        print("\n💡 GỢI Ý HÀNH ĐỘNG:")
        print("  • Dọn nhanh rác an toàn: python cleaner_cli.py --clean --safe-only")
        print("  • Mở Dashboard trực quan: python cleaner_cli.py --web")
    print("=" * 68)

def cmd_clean(args):
    lang = getattr(args, 'lang', 'en')
    print_banner(lang)
    cleaner = AntigravityCleaner()
    use_recycle_bin = not args.permanent

    if args.safe_only:
        mode_str = "[DRY-RUN] " if args.dry_run else ""
        bin_str = ("Windows Recycle Bin" if lang == 'en' else "Thùng rác Windows") if use_recycle_bin else ("Permanent Delete" if lang == 'en' else "Vĩnh viễn")
        
        if lang == 'en':
            print(f"🧹 {mode_str}Cleaning safe items... (Method: {bin_str})")
        else:
            print(f"🧹 {mode_str}Bắt đầu dọn dẹp các mục an toàn... (Phương thức: {bin_str})")
        
        res = cleaner.clean_safe_items(dry_run=args.dry_run, use_recycle_bin=use_recycle_bin)
        print(f"\n✅ Result:" if lang == 'en' else "\n✅ Kết quả:")
        print(f"  • Items processed: {res['deleted_count']}" if lang == 'en' else f"  • Số lượng file/mục đã xử lý: {res['deleted_count']}")
        print(f"  • Space freed: {res['freed_str']}" if lang == 'en' else f"  • Dung lượng giải phóng: {res['freed_str']}")
        if res["errors"]:
            print(f"  ⚠️ Errors ({len(res['errors'])}):")
            for err in res["errors"][:5]:
                print(f"    - {err}")
        else:
            print("  ✨ Completed successfully!" if lang == 'en' else "  ✨ Hoàn tất thành công!")

    elif args.delete_convo:
        cid = args.delete_convo
        print(f"🗑️ Deleting conversation {cid}..." if lang == 'en' else f"🗑️ Đang xoá hoàn toàn hội thoại {cid}...")
        res = cleaner.delete_conversation(cid, dry_run=args.dry_run, use_recycle_bin=use_recycle_bin)
        if res["success"]:
            print(f"✅ Deleted {cid}, freed: {res['freed_str']}" if lang == 'en' else f"✅ Đã xoá {cid}, giải phóng: {res['freed_str']}")
        else:
            print(f"❌ Failed: {res.get('error', res.get('errors'))}")

    elif args.slim_convo:
        cid = args.slim_convo
        print(f"✂️ Slimming conversation {cid}..." if lang == 'en' else f"✂️ Đang tỉa gọn hội thoại {cid}...")
        res = cleaner.slim_conversation(cid, dry_run=args.dry_run, use_recycle_bin=use_recycle_bin)
        if res["success"]:
            print(f"✅ Slimmed {cid}, freed: {res['freed_str']}" if lang == 'en' else f"✅ Đã tỉa gọn {cid}, giải phóng: {res['freed_str']}")
        else:
            print(f"❌ Failed: {res.get('errors')}")

def cmd_vacuum(args):
    lang = getattr(args, 'lang', 'en')
    print_banner(lang)
    print("🗜️ Running SQLite VACUUM..." if lang == 'en' else "🗜️ Đang chạy VACUUM tối ưu hoá database...")
    cleaner = AntigravityCleaner()
    res = cleaner.vacuum_databases()
    if res["success"]:
        print(f"✅ VACUUM complete! Reclaimed {res['freed_str']}" if lang == 'en' else f"✅ VACUUM hoàn tất! Thu hồi thêm {res['freed_str']}")
    else:
        print(f"❌ Failed: {res.get('error')}")

def cmd_web(args):
    import subprocess
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(script_dir, "cleaner_server.py")
    port = str(args.port or 9922)
    print_banner(getattr(args, 'lang', 'en'))
    print(f"🌐 Starting Web Dashboard at http://localhost:{port}...")
    subprocess.call([sys.executable, server_script, "--port", port])

def main():
    parser = argparse.ArgumentParser(description="Antigravity Storage Cleaner CLI")
    parser.add_argument("--scan", action="store_true", help="Scan storage and display summary")
    parser.add_argument("--json", action="store_true", help="Output raw JSON data")
    parser.add_argument("--clean", action="store_true", help="Execute cleanup")
    parser.add_argument("--safe-only", action="store_true", help="Clean only safe items (orphaned DBs, caches)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without deleting")
    parser.add_argument("--permanent", action="store_true", help="Permanent delete (bypasses Recycle Bin)")
    parser.add_argument("--delete-convo", type=str, help="Delete conversation by ID")
    parser.add_argument("--slim-convo", type=str, help="Slim conversation steps/scratch by ID")
    parser.add_argument("--vacuum", action="store_true", help="Run SQLite VACUUM")
    parser.add_argument("--web", action="store_true", help="Launch interactive Web Dashboard")
    parser.add_argument("--port", type=int, default=9922, help="Dashboard port (default: 9922)")
    parser.add_argument("--active-id", type=str, help="Current active conversation ID to protect")
    parser.add_argument("--lang", type=str, choices=['en', 'vi'], default='en', help="Language (en or vi)")

    args = parser.parse_args()

    if args.clean or args.delete_convo or args.slim_convo:
        cmd_clean(args)
    elif args.vacuum:
        cmd_vacuum(args)
    elif args.web:
        cmd_web(args)
    else:
        cmd_scan(args)

if __name__ == "__main__":
    main()
