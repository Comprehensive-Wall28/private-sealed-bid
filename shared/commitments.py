from ecdsa import SECP256k1
import random

# Setup curve parameters
curve = SECP256k1
G = curve.generator
N = curve.order

# Declare H scalar
H_scalar = 0x50929b74c1a04954b78b4b6035e97a5e078a5a0f28ec96d547bfee9ace803ac0
H = G * H_scalar

def generate_commitment_params():
    return G, H

def commit_bid(bid, randomness):
    """
    Creates a Pedersen commitment C = bid * G + randomness * H
    """
    return G * bid + H * randomness

def verify_commitment(C, bid, randomness):
    """
    Verifies that C is a commitment to bid with randomness.
    """
    return C == (G * bid + H * randomness)
