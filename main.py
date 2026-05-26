"""每日推送主入口。

由 CodeBuddy 本地自动化每天 9:00 触发。
也支持手动执行（FORCE=true 绕过防重发检查）。

环境变量：
- BABY_PROFILE_KEY：解密档案的密钥（必须）
- DRY_RUN=1：仅打印不真发
- FORCE=true：忽略防重发，立即发送
"""
from __future__ import annotations

import os
import sys
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.content_picker import pick_today_message, render
from src.profile_store import load_profile
from src.wecom import send

CST = timezone(timedelta(hours=8))
LAST_SENT_FILE = Path(__file__).resolve().parent / "last_sent.txt"


def already_sent_today() -> bool:
    """检查今天是否已经发送过。"""
    if not LAST_SENT_FILE.exists():
        return False
    last = LAST_SENT_FILE.read_text(encoding="utf-8").strip()
    today_str = datetime.now(CST).strftime("%Y-%m-%d")
    return last == today_str


def mark_sent_today():
    """标记今天已发送。"""
    today_str = datetime.now(CST).strftime("%Y-%m-%d")
    LAST_SENT_FILE.write_text(today_str, encoding="utf-8")


def main() -> int:
    try:
        profile = load_profile()
    except RuntimeError as e:
        print(f"[ERROR] 读取档案失败: {e}", file=sys.stderr)
        return 1

    if not profile:
        print("[ERROR] 没有找到档案。", file=sys.stderr)
        return 1

    force = os.environ.get("FORCE", "").lower() == "true"

    if not force and already_sent_today():
        print(f"[gate] 今天已经发过了，跳过。(last_sent={LAST_SENT_FILE.read_text(encoding='utf-8').strip()})")
        return 0

    today = date.today()
    week, day, msg, image_path = pick_today_message(profile, today)
    text = render(profile, week, day, msg, today)

    print("=== 今日消息 ===")
    print(text)
    if image_path:
        print(f"\n[配图] {image_path}")

    if os.environ.get("DRY_RUN") == "1":
        print("\n[DRY_RUN] 不实际发送。")
        return 0

    try:
        result = send(text, image_path)
        print(f"\n[OK] 已推送: {result}")
        mark_sent_today()
        return 0
    except Exception as e:
        print(f"[ERROR] 推送失败: {e}", file=sys.stderr)
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
