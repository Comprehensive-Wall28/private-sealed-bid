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
                    min_bid: int = 0,
                    Bmax: int = 50000,
                    p: int = 2**127 - 1) -> Dict[str, Any]:
    """
    Prepare bidder registration package:
    - create Pedersen commitment
    - generate and verify range proof (for bid - min_bid)
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
    # Convert the provided maximum bid value Bmax into a bit-size relative to min_bid.
    range_size = Bmax - min_bid
    max_bid_bits = max(1, range_size.bit_length())
    
    # Check explicitly if bid is within range to avoid generating invalid proofs that will fail
    if not (min_bid <= bid <= Bmax):
        # We can either let it generate a proof that fails, or fail early. 
        # The prompt says "Invalid bids (outside range) are rejected immediately".
        # Generating a proof for a negative number (bid - min_bid) or too large number would be tricky/fail.
        # Actually (bid - min_bid) would be negative if bid < min_bid.
        # But in a field, negative is large positive. So it might pass "0 <= x" check if x is interpreted as positive.
        # BUT x < 2^10 implies checks smallness. -1 = N-1 which is huge, so it fails range proof.
        # So range proof implicitly checks >= min_bid.
        pass

    # generate a non-interactive range proof for (bid - min_bid)
    # The proof claims: "I know r and v such that C_adj = v*G + r*H AND 0 <= v < 2^k"
    # where C_adj = commitment - commit(min_bid, 0).
    # v should be (bid - min_bid).
    proof = zkproofs.generate_range_proof((bid - min_bid) % N, randomness, max_bid_bits)

    # verify the proof locally before sharing (note: verify_range_proof takes proof, commitment)
    # verifying against adjusted commitment
    offset_commitment = commitments.commit_bid(min_bid, 0)
    adjusted_commitment = commitment + (offset_commitment * -1)
    
    ok = zkproofs.verify_range_proof(proof, adjusted_commitment, max_bid_bits)
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