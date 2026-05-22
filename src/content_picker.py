"""根据档案，从内容库随机抽一条消息并组装。"""
from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path

from .onboarding import calc_week_from_due_date

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "messages.json"


def _load_library() -> dict:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def pick_today_message(profile: dict, today: date | None = None) -> tuple[int, dict]:
    """根据档案选出今天的消息。
    使用 (today.toordinal() + 预产期 hash) 做种子，保证同一天不会重复抽。
    """
    today = today or date.today()
    due = date.fromisoformat(profile["due_date"])
    week = calc_week_from_due_date(due)

    library = _load_library()
    bucket = library.get(str(week)) or library.get("42")  # 兜底

    seed = today.toordinal() * 1000003 + hash(profile["due_date"]) % 100000
    rng = random.Random(seed)
    msg = rng.choice(bucket)

    return week, msg


def render(profile: dict, week: int, msg: dict, today: date | None = None) -> str:
    today = today or date.today()
    due = date.fromisoformat(profile["due_date"])
    days_to_due = (due - today).days
    name = profile.get("name", "亲爱的")

    header = f"💕 {name} | 孕 {week} 周 | 距预产期 {days_to_due} 天\n"
    body = msg["text"]
    footer = "\n\n— 内容仅供参考，具体请以医嘱为准 —"
    return header + body + footer
