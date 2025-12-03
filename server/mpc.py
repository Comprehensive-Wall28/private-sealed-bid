from shared.secret_sharing import reconstruct

def mpc_add(share_a, share_b, p):
    """
    Locally adds two shares.
    """
    return (share_a + share_b) % p

def mpc_sub(share_a, share_b, p):
    """
    Locally subtracts two shares (a - b).
    """
    return (share_a - share_b) % p

def mpc_compare(shares_a, shares_b, p):
    """
    Compares two values given their shares.
    Returns 1 if a > b, -1 if a < b, 0 if a == b.
    
    Protocol:
    1. Compute shares of difference d = a - b.
    2. Reconstruct d.
    3. Check if d is "positive" or "negative" in the field.
       We assume valid bids are small (e.g. < p/2).
       If d < p/2, then a >= b (d is positive).
       If d > p/2, then a < b (d is negative, represented as p - |d|).
    """
    # Each server i computes diff_i = a_i - b_i
    diff_shares = []
    for sa, sb in zip(shares_a, shares_b):
        diff_shares.append(mpc_sub(sa, sb, p))
        
    # 2. Reconstruct difference (Simulating exchange)
    d = reconstruct(diff_shares, p)
    
    # 3. Determine sign
    if d == 0:
        return 0
    elif d < p // 2:
        return 1 # a > b
    else:
        return -1 # a < b

def find_max_bid(bidders, shares_dict, p):
    """
    Finds the maximum bid among bidders.
    bidders: list of bidder IDs
    shares_dict: map of bidder_id -> [s1, s2, s3]
    
    Returns (winner_id, winning_bid)
    """
    if not bidders:
        return None, 0
        
    current_winner = bidders[0]
    current_max_shares = shares_dict[current_winner]
    
    for i in range(1, len(bidders)):
        challenger = bidders[i]
        challenger_shares = shares_dict[challenger]
        
        # Compare current_max vs challenger
        result = mpc_compare(challenger_shares, current_max_shares, p)
        
        if result == 1:
            current_winner = challenger
            current_max_shares = challenger_shares
            
    # Reconstruct the winning bid to return it
    winning_bid = reconstruct(current_max_shares, p)
    return current_winner, winning_bid
