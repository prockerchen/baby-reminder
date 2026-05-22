"""根据档案，按 (week, day) 精确取一条消息。

新内容库结构（content/messages.json）：
{
  "_meta": {...},
  "weeks": {
    "12": {
      "size_label": "一颗青柠 (约 5 cm)",
      "image": "img/week_12.png",  // 可选，本周配图
      "days": [
        {"greeting": "...", "knowledge": "...", "food": "...", "tip": "..."},
        ... 共 7 条 ...
      ]
    },
    ...
  }
}

抽取规则：
- 当前孕周 W、本周第 D 天（D = 1..7）
- 取 weeks[W].days[D-1]
- 第 1 天附图（如果该周配置了 image），其余天数纯文字
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

CONTENT_PATH = Path(__file__).resolve().parent.parent / "content" / "messages.json"


def _load_library() -> dict:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def calc_week_and_day(due_date: date, today: date | None = None) -> tuple[int, int]:
    """根据预产期和今天日期，计算今天是孕第 W 周第 D 天（D = 1..7）。

    医学约定：预产期 = 孕 40 周整（即 280 天）。
    所以今天的孕程总天数 = 280 - (预产期 - 今天).days
    然后 week = 总天数 // 7 + 1, day = 总天数 % 7 + 1
    """
    today = today or date.today()
    days_to_due = (due_date - today).days
    total_days = 280 - days_to_due  # 已经过的孕期天数
    if total_days < 0:
        total_days = 0  # 比 4 周还早，兜底
    week = total_days // 7 + 1
    day = total_days % 7 + 1
    # 范围限制
    if week < 4:
        week, day = 4, 1
    if week > 42:
        week, day = 42, 7
    return week, day


def pick_today_message(profile: dict, today: date | None = None) -> tuple[int, int, dict, str | None]:
    """返回 (week, day, message_dict, image_path_or_None)。"""
    today = today or date.today()
    due = date.fromisoformat(profile["due_date"])
    week, day = calc_week_and_day(due, today)

    library = _load_library()
    weeks = library.get("weeks", {})
    week_data = weeks.get(str(week))
    if not week_data:
        # 找不到就找最近的
        avail = sorted(int(k) for k in weeks.keys())
        if not avail:
            raise RuntimeError("内容库为空")
        nearest = min(avail, key=lambda x: abs(x - week))
        week_data = weeks[str(nearest)]

    days = week_data.get("days", [])
    if not days:
        raise RuntimeError(f"第 {week} 周没有 days 数据")
    msg = days[(day - 1) % len(days)]

    # 是否要附图：仅当本周第 1 天 + 该周配置了 image
    image_path = None
    if day == 1:
        img = week_data.get("image")
        if img:
            full = Path(__file__).resolve().parent.parent / img
            if full.exists():
                image_path = str(full)

    return week, day, msg, image_path


def render(profile: dict, week: int, day: int, msg: dict, today: date | None = None) -> str:
    """组装最终消息文本（markdown 风格）。"""
    today = today or date.today()
    due = date.fromisoformat(profile["due_date"])
    days_to_due = (due - today).days
    name = profile.get("name", "亲爱的")

    lines = [
        f"💕 {name} | 孕 {week} 周第 {day} 天 | 距预产期 {days_to_due} 天",
        "",
        f"🍵 {msg['greeting']}",
        "",
        f"🌱 {msg['knowledge']}",
        "",
        f"🍎 {msg['food']}",
        "",
        f"💡 {msg['tip']}",
        "",
        "— 内容仅供参考，具体请以医嘱为准 —",
    ]
    return "\n".join(lines)
