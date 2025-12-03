from shared.commitments import commit_bid, G, H, N
import hashlib
import random

def hash_points(points):
    """Helper to hash a list of points/values to a scalar."""
    hasher = hashlib.sha256()
    for p in points:
        # Check if p is an ecdsa Point (has x and y methods or attributes)
        if hasattr(p, 'x') and hasattr(p, 'y'):
            # ecdsa points usually have x() and y() methods returning integers
            # or they might be attributes. Let's try to access them safely.
            # In ecdsa library, they are usually methods or properties.
            # We'll convert to string.
            try:
                x_val = p.x()
                y_val = p.y()
            except TypeError:
                x_val = p.x
                y_val = p.y
                
            hasher.update(str(x_val).encode())
            hasher.update(str(y_val).encode())
        else:
            hasher.update(str(p).encode())
    return int(hasher.hexdigest(), 16) % N

def prove_bit(b, r, C):
    """
    Prove that C is a commitment to 0 or 1.
    """
    u = random.randint(0, N-1)
    
    if b == 0:
        # Real proof for C = rH (statement 0)
        # Simulate proof for C - G = rH (statement 1)
        
        # Simulate 1: pick random z1, c1
        z1 = random.randint(0, N-1)
        c1 = random.randint(0, N-1)
        
        # A1 = z1*H - c1*(C - G)
        # In ecdsa, we avoid negative scalars if possible, use (N-x)%N
        # -c1 * (C - G) = (N - c1) * (C + (N-1)*G)
        neg_c1 = (N - c1) % N
        neg_G = (N - 1) * G
        term2 = neg_c1 * (C + neg_G)
        A1 = z1*H + term2
        
        # Commit 0: A0 = u*H
        A0 = u*H
        
        # Challenge
        c = hash_points([C, A0, A1])
        
        # Calculate c0
        c0 = (c - c1) % N
        
        # Response 0: z0 = u + c0*r
        z0 = (u + c0 * r) % N
        
    else: # b == 1
        # Real proof for C - G = rH (statement 1)
        # Simulate proof for C = rH (statement 0)
        
        # Simulate 0: pick random z0, c0
        z0 = random.randint(0, N-1)
        c0 = random.randint(0, N-1)
        # A0 = z0*H - c0*C
        neg_c0 = (N - c0) % N
        A0 = z0*H + neg_c0 * C
        
        # Commit 1: A1 = u*H
        A1 = u*H
        
        # Challenge
        c = hash_points([C, A0, A1])
        
        # Calculate c1
        c1 = (c - c0) % N
        
        # Response 1: z1 = u + c1*r
        z1 = (u + c1 * r) % N

    return (c0, c1, z0, z1)

def verify_bit(C, proof):
    c0, c1, z0, z1 = proof
    
    # Reconstruct A0
    # A0 = z0*H - c0*C
    neg_c0 = (N - c0) % N
    A0 = z0*H + neg_c0 * C
    
    # Reconstruct A1
    # A1 = z1*H - c1*(C - G)
    neg_c1 = (N - c1) % N
    neg_G = (N - 1) * G
    A1 = z1*H + neg_c1 * (C + neg_G)
    
    c = hash_points([C, A0, A1])
    
    return (c0 + c1) % N == c

def generate_range_proof(bid, randomness, max_bid_bits=16):
    """
    Prove that 0 <= bid < 2^max_bid_bits.
    """
    # 1. Bit decomposition
    bits = []
    for i in range(max_bid_bits):
        bits.append((bid >> i) & 1)
        
    # 2. Commit to bits
    bit_commitments = []
    bit_randomness = []
    bit_proofs = []
    
    total_r = 0
    
    for i, b in enumerate(bits):
        r = random.randint(0, N-1)
        bit_randomness.append(r)
        C_bit = commit_bid(b, r)
        bit_commitments.append(C_bit)
        
        proof = prove_bit(b, r, C_bit)
        bit_proofs.append(proof)
        
        # Accumulate randomness scaled by 2^i
        total_r = (total_r + r * (1 << i)) % N

    # 3. Adjustment
    delta_r = (randomness - total_r) % N
    
    # Compute C_sum
    # Initialize with point at infinity? ecdsa doesn't expose it easily as a starting point for sum.
    # We can start with the first term or handle 0 carefully.
    # Or just sum them up.
    # ecdsa points don't support `sum()` with start=0 easily if 0 is integer.
    # We'll iterate.
    
    C_sum = None
    for i, C_bit in enumerate(bit_commitments):
        term = (1 << i) * C_bit
        if C_sum is None:
            C_sum = term
        else:
            C_sum = C_sum + term
            
    # delta_C = C - C_sum
    # delta_C = C + (-1)*C_sum
    neg_C_sum = (N - 1) * C_sum
    delta_C = commit_bid(bid, randomness) + neg_C_sum
    
    # Schnorr proof for delta_C = delta_r * H
    k = random.randint(0, N-1)
    R_point = k * H
    e = hash_points([delta_C, R_point])
    s = (k + e * delta_r) % N
    
    consistency_proof = (e, s)
    
    return {
        'bit_commitments': bit_commitments,
        'bit_proofs': bit_proofs,
        'consistency_proof': consistency_proof
    }

def verify_range_proof(proof, commitment, max_bid_bits=16):
    bit_commitments = proof['bit_commitments']
    bit_proofs = proof['bit_proofs']
    consistency_proof = proof['consistency_proof']
    
    if len(bit_commitments) != max_bid_bits:
        return False
        
    # 1. Verify bit proofs
    for C_bit, p in zip(bit_commitments, bit_proofs):
        if not verify_bit(C_bit, p):
            return False
            
    # 2. Verify consistency
    C_sum = None
    for i, C_bit in enumerate(bit_commitments):
        term = (1 << i) * C_bit
        if C_sum is None:
            C_sum = term
        else:
            C_sum = C_sum + term
            
    neg_C_sum = (N - 1) * C_sum
    delta_C = commitment + neg_C_sum
    
    e, s = consistency_proof
    # R = s*H - e*delta_C
    neg_e = (N - e) % N
    R_point = s * H + neg_e * delta_C
    
    if hash_points([delta_C, R_point]) != e:
        return False
        
    return True
