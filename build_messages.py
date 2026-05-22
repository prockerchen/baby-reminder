"""把 content/parts/*.json 合并成 content/messages.json。
执行：python build_messages.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARTS_DIR = ROOT / "content" / "parts"
OUT_PATH = ROOT / "content" / "messages.json"


def main():
    weeks = {}
    for f in sorted(PARTS_DIR.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for week, week_data in data.items():
            if week in weeks:
                print(f"[WARN] 周 {week} 在多个文件中重复，{f.name} 会覆盖之前的")
            weeks[week] = week_data

    output = {
        "_meta": {
            "version": "2.0",
            "description": "280 天孕期内容库，按 (week, day) 索引",
            "fields": {
                "greeting": "🍵 一句轻松的开场",
                "knowledge": "🌱 今日小知识",
                "food": "🍎 今日饮食推荐",
                "tip": "💡 今日小提醒"
            }
        },
        "weeks": dict(sorted(weeks.items(), key=lambda x: int(x[0])))
    }

    OUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    total_weeks = len(weeks)
    total_days = sum(len(w.get("days", [])) for w in weeks.values())
    print(f"[OK] 合并完成: {total_weeks} 周 / {total_days} 天 → {OUT_PATH}")
    print(f"     覆盖范围: {min(int(k) for k in weeks)} - {max(int(k) for k in weeks)} 周")
    bad = {w: len(d.get("days", [])) for w, d in weeks.items() if len(d.get("days", [])) != 7}
    if bad:
        print(f"[WARN] 不是 7 天的周: {bad}")


if __name__ == "__main__":
    main()
