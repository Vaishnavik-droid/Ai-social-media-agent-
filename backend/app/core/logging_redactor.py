"""
OmniPulse Logging Redaction & Security Utility.
Automatically redacts sensitive parameters from URLs, payloads, dictionaries,
and application logs (client_secret, access_token, refresh_token, code, state, passwords, api_keys).
"""
import logging
import re
from typing import Any, Dict


# Regex patterns matching sensitive credential assignments in URLs, query strings, headers, and JSON
SENSITIVE_PATTERNS = [
    (re.compile(r'(?i)(client_secret|clientsecret|app_secret|secret)=([^&\s]+)'), r'\1=[REDACTED]'),
    (re.compile(r'(?i)(access_token|fb_exchange_token|token)=([^&\s]+)'), r'\1=[REDACTED]'),
    (re.compile(r'(?i)(refresh_token)=([^&\s]+)'), r'\1=[REDACTED]'),
    (re.compile(r'(?i)(code)=([A-Za-z0-9_\-\.]{6,})'), r'\1=[REDACTED]'),
    (re.compile(r'(?i)(state)=([^&\s]+)'), r'\1=[REDACTED]'),
    (re.compile(r'(?i)(api_key|apikey)=([^&\s]+)'), r'\1=[REDACTED]'),
    (re.compile(r'(?i)(authorization:\s*bearer\s+)([A-Za-z0-9_\-\.]{6,})'), r'\1[REDACTED]'),
    (re.compile(r'(?i)("access_token"\s*:\s*)"[^"]+"'), r'\1"[REDACTED]"'),
    (re.compile(r'(?i)("refresh_token"\s*:\s*)"[^"]+"'), r'\1"[REDACTED]"'),
    (re.compile(r'(?i)("client_secret"\s*:\s*)"[^"]+"'), r'\1"[REDACTED]"'),
    (re.compile(r'(?i)("app_secret"\s*:\s*)"[^"]+"'), r'\1"[REDACTED]"'),
    (re.compile(r'(?i)("code"\s*:\s*)"[^"]+"'), r'\1"[REDACTED]"'),
    (re.compile(r'(?i)("state"\s*:\s*)"[^"]+"'), r'\1"[REDACTED]"'),
    (re.compile(r'(?i)("password"\s*:\s*)"[^"]+"'), r'\1"[REDACTED]"'),
    (re.compile(r'(?i)("api_key"\s*:\s*)"[^"]+"'), r'\1"[REDACTED]"'),
]


def redact_sensitive_str(message: str) -> str:
    """Replaces sensitive query parameters and credential tokens with [REDACTED]."""
    if not message:
        return message
    result = str(message)
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def redact_sensitive_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redacts sensitive keys in a dictionary."""
    if not isinstance(data, dict):
        return data
    sanitized = {}
    sensitive_keys = {
        "client_secret", "access_token", "refresh_token", "password",
        "code", "state", "encrypted_access_token", "encrypted_refresh_token",
        "authorization", "token", "secret", "app_secret", "api_key", "apikey"
    }
    for k, v in data.items():
        if k.lower() in sensitive_keys:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = redact_sensitive_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [redact_sensitive_dict(i) if isinstance(i, dict) else i for i in v]
        elif isinstance(v, str):
            sanitized[k] = redact_sensitive_str(v)
        else:
            sanitized[k] = v
    return sanitized


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that intercepts all LogRecords and redacts sensitive credentials
    before they are formatted or written to standard output / log handlers.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            formatted = record.getMessage()
            record.msg = redact_sensitive_str(formatted)
            record.args = ()
        except Exception:
            if isinstance(record.msg, str):
                record.msg = redact_sensitive_str(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = redact_sensitive_dict(record.args)
                elif isinstance(record.args, (tuple, list)):
                    record.args = tuple(
                        redact_sensitive_str(str(a)) for a in record.args
                    )
        if getattr(record, "exc_text", None):
            record.exc_text = redact_sensitive_str(record.exc_text)
        return True
