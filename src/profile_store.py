"""加密/解密用户档案。

档案中可能包含敏感信息（预产期、推送时间、企微 userid），
本地保存为 profile.enc，密钥从环境变量 BABY_PROFILE_KEY 读取。

密钥生成方式：
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

PROFILE_PATH = Path(__file__).resolve().parent.parent / "profile.enc"


def _get_key() -> bytes:
    key = os.environ.get("BABY_PROFILE_KEY")
    if not key:
        raise RuntimeError(
            "环境变量 BABY_PROFILE_KEY 未设置。\n"
            "生成密钥：python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return key.encode()


def save_profile(profile: dict) -> None:
    """加密保存档案到 profile.enc。"""
    f = Fernet(_get_key())
    data = json.dumps(profile, ensure_ascii=False).encode("utf-8")
    token = f.encrypt(data)
    PROFILE_PATH.write_bytes(token)


def load_profile() -> dict | None:
    """读取并解密档案。文件不存在或解密失败返回 None。"""
    if not PROFILE_PATH.exists():
        return None
    try:
        f = Fernet(_get_key())
        token = PROFILE_PATH.read_bytes()
        data = f.decrypt(token)
        return json.loads(data.decode("utf-8"))
    except InvalidToken:
        raise RuntimeError("解密失败：BABY_PROFILE_KEY 与加密时使用的密钥不匹配。")


def profile_exists() -> bool:
    return PROFILE_PATH.exists()
