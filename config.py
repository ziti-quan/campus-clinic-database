# -*- coding: utf-8 -*-
"""项目统一配置：数据库连接与 Flask 会话密钥。

配置来源优先级（前者覆盖后者）：
    1. 真实环境变量
    2. 项目根目录下的 .env 文件（已被 .gitignore 忽略，不会提交到仓库）
    3. 本文件末尾的开发默认值

请不要把真实口令写回源码。首次使用请复制 .env.example 为 .env 再填写。
"""

import os
from pathlib import Path
from urllib.parse import quote

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv(path):
    """极简 .env 读取器：KEY=VALUE，忽略空行与 # 注释，已存在的环境变量优先。"""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_dotenv(BASE_DIR / ".env")

# ------------------------------------------------------------------ 数据库
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3308")
DB_NAME = os.environ.get("DB_NAME", "hospital")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# 如需直接指定完整连接串（例如托管数据库），设置 DATABASE_URL 即可，优先级最高
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
    "mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}".format(
        user=quote(DB_USER, safe=""),
        pwd=quote(DB_PASSWORD, safe=""),
        host=DB_HOST,
        port=DB_PORT,
        db=DB_NAME,
    )
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ------------------------------------------------------------------ 会话密钥
# 部署时请通过环境变量注入随机串，可用：
#     python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
DOCTOR_SECRET_KEY = os.environ.get("DOCTOR_SECRET_KEY", SECRET_KEY + "-doctor")
