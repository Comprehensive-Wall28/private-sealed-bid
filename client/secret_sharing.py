# python
# File: `secret_sharing.py`
import secrets
from typing import Tuple, List

def share_value(value: int, p: int) -> Tuple[int, int, int]:
    """
    Split `value` into three additive shares modulo p.
    Returns (s1, s2, s3) with (s1 + s2 + s3) % p == value % p.
    """
    if not (0 <= value < p):
        value = value % p
    s1 = secrets.randbelow(p)
    s2 = secrets.randbelow(p)
    s3 = (value - s1 - s2) % p
    return s1, s2, s3

def share_bid(bid: int, p: int) -> Tuple[int, int, int]:
    """
    Convenience wrapper for sharing a bid value.
    """
    return share_value(bid, p)