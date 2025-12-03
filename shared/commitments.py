from .ecc import G, H, N
import random

def generate_commitment_params():
    return G, H

def commit_bid(bid, randomness):
    """
    Creates a Pedersen commitment C = bid * G + randomness * H
    """
    return bid * G + randomness * H

def verify_commitment(C, bid, randomness):
    """
    Verifies that C is a commitment to bid with randomness.
    """
    return C == (bid * G + randomness * H)
