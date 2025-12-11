from server.mpc import find_max_bid
from shared.zkproofs import verify_range_proof
from shared.commitments import verify_commitment, N, commit_bid

# Large prime for secret sharing (must be larger than max bid sum, but here max bid is 50000)
P = N 

class AuctionServer:
    def __init__(self, min_bid=0, max_bid=50000):
        self.bidders = []
        self.commitments = {}
        self.shares = {}
        self.verified_bidders = set()
        self.min_bid = min_bid
        self.max_bid = max_bid
        
        # Calculate max_bid_bits for the range [0, max_bid - min_bid]
        range_size = max_bid - min_bid
        self.max_bid_bits = max(1, range_size.bit_length())

    def register_bidder(self, bidder_id):
        if bidder_id not in self.bidders:
            self.bidders.append(bidder_id)
            print(f"Bidder {bidder_id} registered.")

    def receive_commitment_and_proof(self, bidder_id, commitment, proof):
        """
        Receive commitment and ZK range proof from a bidder.
        Verify the proof immediately.
        """
        if bidder_id not in self.bidders:
            raise ValueError("Bidder not registered")
            
        print(f"Verifying proof for bidder {bidder_id}...")
        
        # Adjust commitment to verify against 0-based range proof
        # C_adjusted = C_original - commit(min_bid, 0)
        # Because proof is for (bid - min_bid), and C_original is for bid.
        # C_original = (bid)*G + r*H
        # C_adjusted = (bid - min_bid)*G + r*H
        
        offset_commitment = commit_bid(self.min_bid, 0)
        # Point subtraction: P - Q = P + (-Q)
        # shared/commitments.py uses ecdsa SECP256k1.
        # commitment is a Point. offset_commitment is a Point.
        
        adjusted_commitment = commitment + (offset_commitment * -1)

        if verify_range_proof(proof, adjusted_commitment, self.max_bid_bits):
            self.commitments[bidder_id] = commitment
            self.verified_bidders.add(bidder_id)
            print(f"Bidder {bidder_id} proof verified.")
            return True
        else:
            print(f"Bidder {bidder_id} proof verification FAILED.")
            return False

    def receive_shares(self, bidder_id, shares):
        """
        Receive shares from a bidder.
        'shares' is a list [s1, s2, s3].
        """
        if bidder_id not in self.verified_bidders:
            raise ValueError("Bidder not verified")
            
        self.shares[bidder_id] = shares
        print(f"Received shares from bidder {bidder_id}.")

    def compute_winner(self):
        """
        Run the MPC protocol to find the winner.
        """
        # Filter only bidders who submitted shares
        active_bidders = [b for b in self.bidders if b in self.shares]
        
        if not active_bidders:
            return None, None
            
        print("Computing winner...")
        winner_id, winning_bid = find_max_bid(active_bidders, self.shares, P)
        return winner_id, winning_bid
