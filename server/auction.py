from server.mpc import find_max_bid
from shared.zkproofs import verify_range_proof
from shared.commitments import verify_commitment, N

# Large prime for secret sharing (must be larger than max bid sum, but here max bid is 50000)
# We can use a standard large prime or just N from secp256k1 if we treat shares as scalars on the curve,
# but usually MPC uses a field prime.
# For simplicity and compatibility with our ECC scalars, let's use N (the curve order).
P = N 

class AuctionServer:
    def __init__(self):
        self.bidders = []
        self.commitments = {}
        self.shares = {}
        self.verified_bidders = set()

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
        if verify_range_proof(proof, commitment):
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
        In a real system, each server would receive one share.
        Here, the AuctionServer acts as the coordinator/interface for the 3 servers.
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
