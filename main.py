import sys
import os

# Ensure modules allow importing from current directory
sys.path.append(os.getcwd())

from server.auction import AuctionServer
from client.auction import register_bidder
from shared.commitments import N

def main():
    print("=== Private Sealed-Bid Auction System ===")
    print("Valid Bid Range: 100 to 1000")
    print("Enter 'done' at any prompt to finish bidding and calculate winner.")
    
    # Initialize Server with required range
    MIN_BID = 100
    MAX_BID = 1000
    server = AuctionServer(min_bid=MIN_BID, max_bid=MAX_BID)
    
    while True:
        print("\n--- New Bidder ---")
        bidder_id = input("Enter Bidder ID: ").strip()
        if bidder_id.lower() == 'done':
            break
        
        if not bidder_id:
            print("Bidder ID cannot be empty.")
            continue
            
        bid_str = input(f"Enter Bid Amount (integer {MIN_BID}-{MAX_BID}): ").strip()
        if bid_str.lower() == 'done':
            break
            
        try:
            bid = int(bid_str)
        except ValueError:
            print("Invalid bid amount. Please enter an integer.")
            continue
            
        print(f"Processing bid for {bidder_id}...")
        
        # Ensure bidder is registered on server
        server.register_bidder(bidder_id)
        
        try:
            # 1. Client: Prepare registration package (Commitment + ZK Proof + Shares)
            #    This simulates the code running on the User's device.
            client_data = register_bidder(bidder_id, bid, min_bid=MIN_BID, Bmax=MAX_BID, p=N)
            
            # 2. Server: Verify Commitment and ZK Proof
            #    This simulates the Server receiving the data.
            is_valid = server.receive_commitment_and_proof(
                client_data['id'], 
                client_data['commitment'], 
                client_data['proof']
            )
            
            if is_valid:
                # 3. Server: Store Shares (only if proof valid)
                server.receive_shares(client_data['id'], client_data['shares'])
                print(f"-> Success: Bid accepted for {bidder_id}.")
            else:
                print(f"-> Rejected: ZK Range Proof failed for {bidder_id}.")
                
        except ValueError as e:
            # Client-side verification failure (e.g. proof generation check)
            print(f"-> Error: {e}")
        except Exception as e:
            print(f"-> Unexpected Error: {e}")

        cont = input("\nAdd another bidder? (Y/n): ").strip().lower()
        if cont == 'n' or cont == 'no' or cont == 'done':
            break

    print("\n=== Bidding Closed ===")
    print("Computing Winner via MPC...")
    winner_id, winner_bid = server.compute_winner()
    
    if winner_id is not None:
        print(f"\nWINNER: Bidder '{winner_id}' with Bid Amount: {winner_bid}")
    else:
        print("\nNo valid bids were received.")

if __name__ == "__main__":
    main()
