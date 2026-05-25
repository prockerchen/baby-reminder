"""每日推送主入口（在 GitHub Actions 里被 cron 触发）。

环境变量：
- BABY_PROFILE_KEY：解密档案的密钥（必须）
- 企微推送凭证：
  - WECOM_WEBHOOK_KEY（推荐，群机器人，无 IP 限制）
- DRY_RUN=1：仅打印不真发，便于调试
- FORCE=true：忽略时间检查，立即发送（手动触发时使用）

时间网关 + 防重发：
- 每天只发一次（用 last_sent.txt 记录）
- 当前北京时间小时 == profile.push_time 的小时，才会发
- 提供 30 分钟容差：如果当天 push 时间已经过去但还没发，补发
"""
from __future__ import annotations

import os
import sys
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# 让脚本无论从哪里被调用都能找到 src 包
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.content_picker import pick_today_message, render
from src.profile_store import load_profile
from src.wecom import send

CST = timezone(timedelta(hours=8))
LAST_SENT_FILE = Path(__file__).resolve().parent / "last_sent.txt"


def should_send_today(push_time: str, force: bool) -> tuple[bool, str]:
    """判断是否应该现在发送。返回 (是否发送, 原因日志)。"""
    if force:
        return True, "[gate] FORCE=true，强制发送"

    now_cst = datetime.now(CST)
    today_str = now_cst.strftime("%Y-%m-%d")

    # 防重发：如果今天已经发过了，跳过
    if LAST_SENT_FILE.exists():
        last = LAST_SENT_FILE.read_text(encoding="utf-8").strip()
        if last == today_str:
            return False, f"[gate] 今天 {today_str} 已经发过了，跳过"

    target_hour = int(push_time.split(":")[0])
    target_minute = int(push_time.split(":")[1]) if ":" in push_time else 0

    # 当前时间是否 >= 用户设定的发送时间（同一天）
    target_dt = now_cst.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

    if now_cst >= target_dt:
        return True, f"[gate] 当前 {now_cst:%H:%M} >= 设定 {push_time}，且今天还没发，发送"
    else:
        return False, f"[gate] 当前 {now_cst:%H:%M} < 设定 {push_time}，等会再发"


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
    push_time = profile.get("push_time", "08:00")

    should, reason = should_send_today(push_time, force)
    print(reason)
    if not should:
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
        # 同步把 last_sent 提交回仓库（让下次 run 知道今天已发）
        _try_commit_last_sent()
        return 0
    except Exception as e:
        print(f"[ERROR] 推送失败: {e}", file=sys.stderr)
        traceback.print_exc()
        return 2


def _try_commit_last_sent():
    """在 GitHub Actions 里把 last_sent.txt commit 回去。"""
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    import subprocess
    try:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
        subprocess.run(["git", "add", "last_sent.txt"], check=True)
        subprocess.run(["git", "commit", "-m", f"chore: mark sent {datetime.now(CST):%Y-%m-%d}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("[OK] last_sent.txt 已提交回仓库")
    except subprocess.CalledProcessError as e:
        print(f"[WARN] 提交 last_sent.txt 失败（不阻塞）: {e}")


if __name__ == "__main__":
    sys.exit(main())
