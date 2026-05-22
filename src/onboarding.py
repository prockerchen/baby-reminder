"""首次使用引导：询问预产期/孕周和推送时间，加密保存。

使用方式：
    python -m src.onboarding
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from .profile_store import load_profile, save_profile


def _ask(prompt: str) -> str:
    return input(prompt).strip()


def _parse_date(s: str) -> date:
    """支持 2026-12-01 / 2026/12/01 / 2026.12.01 / 20261201 等格式。"""
    s = re.sub(r"[./_]", "-", s)
    s = re.sub(r"-+", "-", s)
    if "-" not in s and len(s) == 8:
        s = f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return datetime.strptime(s, "%Y-%m-%d").date()


def _parse_time(s: str) -> str:
    """支持 8 / 8:00 / 08:00 / 8点 / 8点30 等格式，返回 HH:MM。"""
    s = s.replace("：", ":").replace("点", ":").strip()
    if s.endswith(":"):
        s = s[:-1]
    if ":" not in s:
        s = f"{s}:00"
    h, m = s.split(":", 1)
    h_int = int(h)
    m_int = int(m) if m else 0
    if not (0 <= h_int <= 23 and 0 <= m_int <= 59):
        raise ValueError("时间不合法")
    return f"{h_int:02d}:{m_int:02d}"


def calc_due_date_from_week(current_week: int) -> date:
    """根据当前孕周反推预产期：默认按今天处于该周第 0 天。
    预产期 = 今天 + (40 - week) * 7 天
    """
    today = date.today()
    return today + timedelta(days=(40 - current_week) * 7)


def calc_week_from_due_date(due: date) -> int:
    """根据预产期计算今日孕周。"""
    today = date.today()
    days_to_due = (due - today).days
    week = 40 - days_to_due // 7
    return max(4, min(42, week))


def run() -> dict:
    print("\n========== 宝宝提醒 · 首次使用 ==========\n")
    print("我会帮你保存一份只在本地加密存储的档案，用于每天给你发一条贴心消息。\n")

    existing = None
    try:
        existing = load_profile()
    except RuntimeError as e:
        if "BABY_PROFILE_KEY" in str(e):
            print("⚠️  请先设置环境变量 BABY_PROFILE_KEY 再运行本程序。")
            print("    生成密钥示例：")
            print('    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"\n')
            raise SystemExit(1)

    if existing:
        print("检测到已有档案：")
        print(f"  预产期：{existing.get('due_date')}")
        print(f"  推送时间：{existing.get('push_time')}\n")
        if _ask("要重新设置吗？(y/N): ").lower() != "y":
            return existing

    print("第 1 题：你知道预产期吗？")
    print("  1) 知道，输入预产期日期")
    print("  2) 不知道，但知道现在是第几周")
    while True:
        choice = _ask("请选择 (1/2): ")
        if choice in ("1", "2"):
            break
        print("请输入 1 或 2。")

    if choice == "1":
        while True:
            try:
                s = _ask("请输入预产期（如 2026-12-01）: ")
                due_date = _parse_date(s)
                if due_date < date.today():
                    print("预产期不能早于今天，请重新输入。")
                    continue
                break
            except ValueError:
                print("日期格式不对，请用 2026-12-01 这样的格式。")
    else:
        while True:
            try:
                w = int(_ask("请输入当前孕周（4-42）: "))
                if 4 <= w <= 42:
                    due_date = calc_due_date_from_week(w)
                    print(f"  → 推算出的预产期：{due_date}")
                    break
                print("请输入 4-42 之间的整数。")
            except ValueError:
                print("请输入数字。")

    print("\n第 2 题：每天什么时候推送？")
    while True:
        try:
            t = _ask("请输入推送时间（如 08:00 / 9点 / 21:30）: ")
            push_time = _parse_time(t)
            break
        except (ValueError, IndexError):
            print("时间格式不对，请用 08:00 这样的格式。")

    name = _ask("\n第 3 题（可选）：你想被怎么称呼？回车跳过: ") or "亲爱的"

    profile = {
        "due_date": due_date.isoformat(),
        "push_time": push_time,
        "name": name,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }

    save_profile(profile)

    week_now = calc_week_from_due_date(due_date)
    print("\n========== 设置完成 ==========")
    print(f"  ✓ 预产期：{due_date}")
    print(f"  ✓ 推送时间：{push_time}")
    print(f"  ✓ 称呼：{name}")
    print(f"  ✓ 当前孕周：第 {week_now} 周")
    print(f"\n档案已加密保存。明天 {push_time} 起，会准时收到第一条消息~\n")

    return profile


if __name__ == "__main__":
    run()
