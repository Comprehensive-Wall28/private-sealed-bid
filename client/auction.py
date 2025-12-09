# python
# File: `auction.py`
from typing import Dict, Any
import secrets

from shared import commitments, zkproofs
from . import secret_sharing

# Use curve group order when sampling randomness
N = commitments.N

def register_bidder(bidder_id: str,
                    bid: int,
                    randomness: int = None,
                    Bmax: int = 50000,
                    p: int = 2**127 - 1) -> Dict[str, Any]:
    """
    Prepare bidder registration package:
    - create Pedersen commitment
    - generate and verify range proof
    - split bid into 3 additive shares modulo p

    Returns a dictionary with keys: 'id', 'commitment', 'proof', 'shares'
    Raises ValueError if the range proof verification fails.
    """
    # randomness should be a scalar in the curve group order
    if randomness is None:
        randomness = secrets.randbelow(N)

    # create commitment (expects commitments.commit_bid(bid, randomness) in project)
    commitment = commitments.commit_bid(bid, randomness)

    # The shared/zkproofs API expects `max_bid_bits` (proof bounds 0 <= b < 2^bits).
    # Convert the provided maximum bid value Bmax into a bit-size.
    max_bid_bits = max(1, Bmax.bit_length())

    # generate a non-interactive range proof
    proof = zkproofs.generate_range_proof(bid, randomness, max_bid_bits)

    # verify the proof locally before sharing (note: verify_range_proof takes proof, commitment)
    ok = zkproofs.verify_range_proof(proof, commitment, max_bid_bits)
    if not ok:
        raise ValueError("Range proof verification failed; bid rejected.")

    # create additive shares
    shares = secret_sharing.share_bid(bid, p)

    return {
        "id": bidder_id,
        "commitment": commitment,
        "proof": proof,
        "shares": shares
    }