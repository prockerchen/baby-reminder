"""企业微信推送封装。

支持两种模式（环境变量自动选择）：
1. 自建应用消息（推荐 1v1 体验）：需要 WECOM_CORP_ID / WECOM_AGENT_ID / WECOM_SECRET / WECOM_TOUSER
2. 群机器人 webhook（最简单）：需要 WECOM_WEBHOOK_KEY
"""
from __future__ import annotations

import os
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


def _send_webhook(text: str) -> dict[str, Any]:
    key = os.environ["WECOM_WEBHOOK_KEY"]
    url = f"{WECOM_API}/webhook/send?key={key}"
    payload = {"msgtype": "text", "text": {"content": text}}
    resp = requests.post(url, json=payload, timeout=10)
    data = resp.json()
    if data.get("errcode") != 0:
        raise WeComError(f"Webhook 发送失败: {data}")
    return data


def send(text: str) -> dict[str, Any]:
    """根据环境变量自动选择推送方式。"""
    if os.environ.get("WECOM_CORP_ID") and os.environ.get("WECOM_SECRET"):
        return _send_app_message(text)
    if os.environ.get("WECOM_WEBHOOK_KEY"):
        return _send_webhook(text)
    raise WeComError(
        "没有配置任何企微推送凭证。请设置以下任一组环境变量：\n"
        "  应用消息: WECOM_CORP_ID + WECOM_AGENT_ID + WECOM_SECRET (+ WECOM_TOUSER)\n"
        "  群机器人: WECOM_WEBHOOK_KEY"
    )
