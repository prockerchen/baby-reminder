"""每日推送主入口（在 GitHub Actions 里被 cron 触发）。

环境变量：
- BABY_PROFILE_KEY：解密档案的密钥（必须）
- 企微推送凭证（任一组）：
  - WECOM_CORP_ID + WECOM_AGENT_ID + WECOM_SECRET + WECOM_TOUSER
  - WECOM_WEBHOOK_KEY
- DRY_RUN=1：仅打印不真发，便于调试
"""
from __future__ import annotations

import os
import sys
import traceback
from datetime import date
from pathlib import Path

# 让脚本无论从哪里被调用都能找到 src 包（兼容中文路径下的 PYTHONPATH 问题）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.content_picker import pick_today_message, render
from src.profile_store import load_profile
from src.wecom import send


def main() -> int:
    try:
        profile = load_profile()
    except RuntimeError as e:
        print(f"[ERROR] 读取档案失败: {e}", file=sys.stderr)
        return 1

    if not profile:
        print("[ERROR] 没有找到档案。请先在本地运行 `python -m src.onboarding` 完成首次设置，"
              "并把生成的 profile.enc 提交到仓库。", file=sys.stderr)
        return 1

    today = date.today()
    week, msg = pick_today_message(profile, today)
    text = render(profile, week, msg, today)

    print("=== 今日消息 ===")
    print(text)
    print("=== 风格 ===", msg.get("style", "未知"))

    if os.environ.get("DRY_RUN") == "1":
        print("\n[DRY_RUN] 不实际发送。")
        return 0

    try:
        result = send(text)
        print(f"\n[OK] 已推送: {result}")
        return 0
    except Exception as e:
        print(f"[ERROR] 推送失败: {e}", file=sys.stderr)
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
