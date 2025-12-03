import random

def share_bid(bid, p):
    """
    Splits bid into 3 additive shares modulo p.
    bid = s1 + s2 + s3 mod p
    """
    s1 = random.randint(0, p - 1)
    s2 = random.randint(0, p - 1)
    s3 = (bid - s1 - s2) % p
    return [s1, s2, s3]

def reconstruct(shares, p):
    """
    Reconstructs the value from additive shares.
    value = sum(shares) mod p
    """
    return sum(shares) % p
