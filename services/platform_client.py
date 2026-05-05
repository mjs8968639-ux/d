"""
平台 API 请求客户端（通用封装）。
当前支持：
- 参数拼装
- MD5/SHA256 签名
- 真实请求或 mock 回退
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SENSITIVE_KEYS = {"sign", "client_secret", "secret", "app_secret", "access_token", "token"}


@dataclass(frozen=True)
class PlatformRequestSpec:
    base_url: str
    method_param: str
    sign_style: str  # pdd | taobao | jd
    sign_secret_env: str
    app_key_env: str


class PlatformClientError(RuntimeError):
    pass


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def _build_unix_timestamp() -> str:
    return str(int(time.time()))


def _sign_pdd(params: Mapping[str, Any], secret: str) -> str:
    items = [f"{k}{params[k]}" for k in sorted(params) if k not in {"sign", "access_token"} and params[k] not in (None, "")]
    raw = f"{secret}{''.join(items)}{secret}"
    return _md5(raw).upper()


def _sign_taobao(params: Mapping[str, Any], secret: str) -> str:
    items = [f"{k}{params[k]}" for k in sorted(params) if k not in {"sign", "access_token"} and params[k] not in (None, "")]
    raw = f"{secret}{''.join(items)}{secret}"
    return _md5(raw).upper()


def _sign_jd(params: Mapping[str, Any], secret: str) -> str:
    items = [f"{k}{params[k]}" for k in sorted(params) if k not in {"sign"} and params[k] not in (None, "")]
    raw = f"{secret}{''.join(items)}{secret}"
    return _md5(raw).upper()


def build_signed_params(spec: PlatformRequestSpec, method: str, extra_params: Mapping[str, Any]) -> dict[str, Any]:
    app_key = os.getenv(spec.app_key_env, "").strip()
    secret = os.getenv(spec.sign_secret_env, "").strip()
    if not app_key or not secret:
        raise PlatformClientError(f"缺少平台配置：{spec.app_key_env} / {spec.sign_secret_env}")

    params: dict[str, Any] = dict(extra_params)
    params[spec.method_param] = method

    if spec.sign_style == "pdd":
        params["timestamp"] = params.get("timestamp") or _build_unix_timestamp()
        params["type"] = method
        params["client_id"] = app_key
        params.setdefault("data_type", "JSON")
        params["sign"] = _sign_pdd(params, secret)
    elif spec.sign_style == "taobao":
        params["timestamp"] = params.get("timestamp") or _build_timestamp()
        params["app_key"] = app_key
        params.setdefault("format", "json")
        params.setdefault("v", "2.0")
        params.setdefault("sign_method", "md5")
        params["sign"] = _sign_taobao(params, secret)
    elif spec.sign_style == "jd":
        params["timestamp"] = params.get("timestamp") or _build_timestamp()
        params.setdefault("v", "1.0")
        params.setdefault("format", "json")
        params["app_key"] = app_key
        params["appKey"] = app_key
        params["sign"] = _sign_jd(params, secret)
    else:
        raise PlatformClientError(f"不支持的签名方式：{spec.sign_style}")

    return params


def send_get(url: str, params: Mapping[str, Any]) -> dict[str, Any]:
    query = urlencode({k: "" if v is None else str(v) for k, v in params.items()})
    req = Request(f"{url}?{query}", method="GET")
    with urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
    return _parse_json(body)


def send_post(url: str, params: Mapping[str, Any]) -> dict[str, Any]:
    data = urlencode({k: "" if v is None else str(v) for k, v in params.items()}).encode("utf-8")
    req = Request(url, data=data, method="POST")
    with urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
    return _parse_json(body)


def debug_get(url: str, params: Mapping[str, Any]) -> dict[str, Any]:
    query = urlencode({k: "" if v is None else str(v) for k, v in params.items()})
    request_url = f"{url}?{query}"
    try:
        response = send_get(url, params)
        return {"ok": True, "request_url": _mask_url(request_url), "params": mask_sensitive_params(params), "response": response}
    except Exception as exc:
        return {"ok": False, "request_url": _mask_url(request_url), "params": mask_sensitive_params(params), "error": str(exc)}


def debug_post(url: str, params: Mapping[str, Any]) -> dict[str, Any]:
    try:
        response = send_post(url, params)
        return {"ok": True, "request_url": url, "params": mask_sensitive_params(params), "response": response}
    except Exception as exc:
        return {"ok": False, "request_url": url, "params": mask_sensitive_params(params), "error": str(exc)}


def mask_sensitive_params(params: Mapping[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for key, value in params.items():
        if key.lower() in SENSITIVE_KEYS or "secret" in key.lower():
            masked[key] = _mask_value(str(value))
        else:
            masked[key] = value
    return masked


def _mask_url(url: str) -> str:
    return url.replace("sign=", "sign=***")


def _mask_value(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}***{value[-4:]}"


def _parse_json(body: str) -> dict[str, Any]:
    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}
    except Exception as exc:
        raise PlatformClientError(f"平台响应不是合法 JSON: {body[:200]}") from exc
