import random

# secp256k1 parameters
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
A = 0
B = 7
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

class Point:
    def __init__(self, x, y, infinity=False):
        self.x = x
        self.y = y
        self.infinity = infinity

    def __eq__(self, other):
        if self.infinity:
            return other.infinity
        if other.infinity:
            return False
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        if self.infinity:
            return "Point(infinity)"
        return f"Point({hex(self.x)}, {hex(self.y)})"

    def __add__(self, other):
        if self.infinity:
            return other
        if other.infinity:
            return self

        if self.x == other.x and self.y != other.y:
            return Point(0, 0, True)

        if self.x == other.x and self.y == other.y:
            if self.y == 0:
                return Point(0, 0, True)
            lam = (3 * self.x * self.x + A) * pow(2 * self.y, P - 2, P) % P
        else:
            lam = (other.y - self.y) * pow(other.x - self.x, P - 2, P) % P

        x3 = (lam * lam - self.x - other.x) % P
        y3 = (lam * (self.x - x3) - self.y) % P
        return Point(x3, y3)

    def __neg__(self):
        if self.infinity:
            return self
        return Point(self.x, -self.y % P)

    def __sub__(self, other):
        return self + (-other)

    def __mul__(self, n):
        if n == 0:
            return Point(0, 0, True)
        
        if n < 0:
            return (-self) * (-n)
        
        current = self
        result = Point(0, 0, True)
        while n > 0:
            if n % 2 == 1:
                result = result + current
            current = current + current
            n //= 2
        return result
    
    def __rmul__(self, n):
        return self * n

G = Point(Gx, Gy)

# Generate a second generator H deterministically for Pedersen commitments
# In a real system, this should be generated such that log_G(H) is unknown.
# For this simplified project, we can hash G to find H, or just pick a random point.
# We'll pick a random scalar and multiply G, but pretend we don't know it for the sake of the protocol structure,
# OR better, use a standard nothing-up-my-sleeve number.
# For simplicity here, let's just take G * 123456789 (in reality, H's discrete log must be unknown).
# To be slightly more "secure" in spirit, we could try to find a point from a hash, but that's complex to implement from scratch.
# We will use a fixed random scalar for H to ensure it's a valid point.
H = G * 0x50929b74c1a04954b78b4b6035e97a5e078a5a0f28ec96d547bfee9ace803ac0 
