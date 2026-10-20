"""Compatibility exports for the individual rule modules."""
from .account_compromise import AccountCompromiseRule
from .file_activity import FileActivityRule
from .suspicious_process import SuspiciousProcessRule

__all__ = ["AccountCompromiseRule", "SuspiciousProcessRule", "FileActivityRule"]
