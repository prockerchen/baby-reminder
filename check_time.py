"""判断当前时刻是否到了用户设定的推送时间。
GitHub Actions cron 每小时触发一次，本脚本判断"当前北京时间小时"是否匹配。
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.profile_store import load_profile

CST = timezone(timedelta(hours=8))


def main() -> int:
    profile = load_profile()
    if not profile:
        print("[gate] 没有档案，跳过。")
        return 1  # 用 1 让 workflow 后续步骤跳过

    push_time = profile.get("push_time", "08:00")
    target_hour = int(push_time.split(":")[0])

    now_cst = datetime.now(CST)
    print(f"[gate] 当前北京时间: {now_cst:%Y-%m-%d %H:%M}, 目标推送小时: {target_hour:02d}")

    if now_cst.hour == target_hour:
        print("[gate] 命中推送时间，继续。")
        return 0
    print("[gate] 未到推送时间，跳过。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
