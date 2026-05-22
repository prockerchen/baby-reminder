"""企业微信推送封装。

支持两种模式（环境变量自动选择）：
1. 自建应用消息（推荐 1v1 体验）：需要 WECOM_CORP_ID / WECOM_AGENT_ID / WECOM_SECRET / WECOM_TOUSER
2. 群机器人 webhook（最简单）：需要 WECOM_WEBHOOK_KEY

群机器人支持图片消息（base64 + md5）。
"""
from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from typing import Any

import requests

WECOM_API = "https://qyapi.weixin.qq.com/cgi-bin"


class WeComError(RuntimeError):
    pass


def _get_access_token(corp_id: str, secret: str) -> str:
    url = f"{WECOM_API}/gettoken"
    resp = requests.get(url, params={"corpid": corp_id, "corpsecret": secret}, timeout=10)
    data = resp.json()
    if data.get("errcode") != 0:
        raise WeComError(f"获取 access_token 失败: {data}")
    return data["access_token"]


def _send_app_message(text: str) -> dict[str, Any]:
    corp_id = os.environ["WECOM_CORP_ID"]
    agent_id = int(os.environ["WECOM_AGENT_ID"])
    secret = os.environ["WECOM_SECRET"]
    touser = os.environ.get("WECOM_TOUSER", "@all")

    token = _get_access_token(corp_id, secret)
    url = f"{WECOM_API}/message/send?access_token={token}"
    payload = {
        "touser": touser,
        "msgtype": "text",
        "agentid": agent_id,
        "text": {"content": text},
        "safe": 0,
    }
    resp = requests.post(url, json=payload, timeout=10)
    data = resp.json()
    if data.get("errcode") != 0:
        raise WeComError(f"应用消息发送失败: {data}")
    return data


def _webhook_post(payload: dict) -> dict[str, Any]:
    key = os.environ["WECOM_WEBHOOK_KEY"]
    url = f"{WECOM_API}/webhook/send?key={key}"
    resp = requests.post(url, json=payload, timeout=10)
    data = resp.json()
    if data.get("errcode") != 0:
        raise WeComError(f"Webhook 发送失败: {data}")
    return data


def _send_webhook_text(text: str) -> dict[str, Any]:
    return _webhook_post({"msgtype": "text", "text": {"content": text}})


def _send_webhook_image(image_path: str) -> dict[str, Any]:
    """发送图片消息。企微限制：单图 2MB 以内，仅支持 jpg/png。"""
    p = Path(image_path)
    if not p.exists():
        raise WeComError(f"图片不存在: {image_path}")
    raw = p.read_bytes()
    if len(raw) > 2 * 1024 * 1024:
        raise WeComError(f"图片超过 2MB，需压缩: {image_path} ({len(raw)} bytes)")
    b64 = base64.b64encode(raw).decode("ascii")
    md5 = hashlib.md5(raw).hexdigest()
    return _webhook_post({
        "msgtype": "image",
        "image": {"base64": b64, "md5": md5}
    })


def send(text: str, image_path: str | None = None) -> dict[str, Any]:
    """根据环境变量自动选择推送方式。
    优先级：webhook > 应用消息

    如果提供了 image_path，会先发文字再发图片（webhook 模式下），
    这样消息列表展示时是「先看到关怀文案 → 再看到配图」的节奏，
    符合阅读直觉。
    """
    if os.environ.get("WECOM_WEBHOOK_KEY"):
        results = {}
        results["text"] = _send_webhook_text(text)
        if image_path:
            try:
                results["image"] = _send_webhook_image(image_path)
            except Exception as e:
                # 图片发失败不阻止文本（文本已经发出去了）
                results["image_error"] = str(e)
        return results
    if os.environ.get("WECOM_CORP_ID") and os.environ.get("WECOM_SECRET"):
        # 应用消息暂不支持图片，只发文本（图片需要先上传素材，私人项目省略）
        return _send_app_message(text)
    raise WeComError(
        "没有配置任何企微推送凭证。请设置以下任一组环境变量：\n"
        "  群机器人（推荐）: WECOM_WEBHOOK_KEY\n"
        "  应用消息: WECOM_CORP_ID + WECOM_AGENT_ID + WECOM_SECRET (+ WECOM_TOUSER)"
    )
