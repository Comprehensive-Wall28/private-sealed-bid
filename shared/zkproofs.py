from shared.ecc import G, H, N, Point
from shared.commitments import commit_bid
import hashlib
import random

def hash_points(points):
    """Helper to hash a list of points/values to a scalar."""
    hasher = hashlib.sha256()
    for p in points:
        if isinstance(p, Point):
            hasher.update(str(p.x).encode())
            hasher.update(str(p.y).encode())
        else:
            hasher.update(str(p).encode())
    return int(hasher.hexdigest(), 16) % N

def prove_bit(b, r, C):
    """
    Prove that C is a commitment to 0 or 1.
    b: the bit (0 or 1)
    r: randomness used in C
    C: the commitment C = bG + rH
    
    We use a ring signature or OR-proof logic.
    Prove knowledge of (b, r) such that C = bG + rH AND (b=0 OR b=1).
    Equivalent to:
    Proving knowledge of r s.t. C = rH  (if b=0)
    OR
    Proving knowledge of r s.t. C - G = rH (if b=1)
    """
    # This is a standard "1-out-of-2" ZK proof (Cramer-Shoup-like or Sigma OR-proof).
    # We want to prove we know r' such that C' = r'H, where C' is either C or C-G.
    
    # Let's use a simple simulation-based OR proof.
    # We have two challenges c0, c1. We control one.
    
    # If b=0: We know r for C = rH. We simulate proof for C-G.
    # If b=1: We know r for C-G = rH. We simulate proof for C.
    
    u = random.randint(0, N-1)
    
    if b == 0:
        # Real proof for C = rH (statement 0)
        # Simulate proof for C - G = rH (statement 1)
        
        # Simulate 1: pick random z1, c1
        z1 = random.randint(0, N-1)
        c1 = random.randint(0, N-1)
        # A1 = z1*H - c1*(C - G)
        A1 = z1*H + (-c1) * (C + (-1)*G)
        
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
        A0 = z0*H + (-c0) * C
        
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
    A0 = z0*H + (-c0) * C
    
    # Reconstruct A1
    # A1 = z1*H - c1*(C - G)
    A1 = z1*H + (-c1) * (C + (-1)*G)
    
    c = hash_points([C, A0, A1])
    
    return (c0 + c1) % N == c

def generate_range_proof(bid, randomness, max_bid_bits=16):
    """
    Prove that 0 <= bid < 2^max_bid_bits.
    Decompose bid into bits. Commit to each bit. Prove each is a bit.
    Show sum of commitments matches total commitment.
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
        # Total C should be sum(2^i * C_bit)
        # Total C = sum(2^i * (b_i*G + r_i*H)) = sum(b_i*2^i)*G + sum(r_i*2^i)*H
        # We need to adjust the final randomness to match the input 'randomness'
        total_r = (total_r + r * (1 << i)) % N

    # 3. Adjustment
    # The sum of bit commitments is C_sum = bid*G + total_r*H
    # The actual commitment is C = bid*G + randomness*H
    # We need to prove that C and C_sum commit to the same value (bid).
    # i.e., C - C_sum = (randomness - total_r) * H
    # This is a knowledge of discrete log proof for (C - C_sum) base H.
    
    delta_r = (randomness - total_r) % N
    
    # Compute C_sum
    C_sum = Point(0, 0, True)
    for i, C_bit in enumerate(bit_commitments):
        C_sum = C_sum + (1 << i) * C_bit
        
    delta_C = commit_bid(bid, randomness) + (-1) * C_sum # Should be delta_r * H
    
    # Schnorr proof for delta_C = delta_r * H
    # k = random
    # R = k*H
    # e = hash(delta_C, R)
    # s = k + e * delta_r
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
    # Reconstruct C_sum
    C_sum = Point(0, 0, True)
    for i, C_bit in enumerate(bit_commitments):
        C_sum = C_sum + (1 << i) * C_bit
        
    delta_C = commitment + (-1) * C_sum
    
    e, s = consistency_proof
    # s*H = k*H + e*delta_r*H = R + e*delta_C
    # R = s*H - e*delta_C
    R_point = s * H + (-e) * delta_C
    
    if hash_points([delta_C, R_point]) != e:
        return False
        
    return True
