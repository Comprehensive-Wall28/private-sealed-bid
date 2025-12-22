# Privacy-Preserving Private Sealed-Bid Auction Documentation

This document explains the cryptographic architecture and integration of the Private Sealed-Bid Auction system. The system ensures that bid values remain confidential throughout the auction process, with only the winning bidder and amount revealed at the end, using a **3-party Secure Multi-Party Computation (MPC)** architecture.

## 1. System Overview

The system consists of:
*   **Bidders**: Clients who submit bids.
*   **Three Servers (S1, S2, S3)**: Computation nodes that process shares of the bids without ever seeing the raw bid values.

### Core Workflow
1.  **Commitment**: Bidders commit to their bid to ensure binding.
2.  **Validation**: Bidders prove their bid is within the valid range (e.g., [100, 1000]) using Zero-Knowledge Proofs (ZKP), without revealing the bid.
3.  **Secret Sharing**: Valid bids are split into 3 shares and distributed to the servers.
4.  **MPC Computation**: Servers cooperate to determine the maximum bid (winner) using MPC comparison protocols on the shares.

---

## 2. Cryptographic Components

### A. Elliptic-Curve Pedersen Commitments
Used to bind a bidder to a value without revealing it.
*   **Setup**: Generator points $G$ and $H$ on the SECP256k1 curve, where the discrete log $\log_G H$ is unknown.
*   **Commitment**: $C = b \cdot G + r \cdot H$
    *   $b$: Bid amount
    *   $r$: Random blinding factor
*   **Property**: Perfectly hiding (due to $r$) and computationally binding (cannot change $b$ without solving discrete log).

### B. Zero-Knowledge Range Proofs
Ensures that a committed bid $b$ lies within the allowed range $[min, max]$ (e.g., $100 \le b \le 1000$).
*   **Technique**: Bit Decomposition combined with Commitments and Fiat-Shamir heuristic.
*   **Implementation**:
    1.  The range is shifted: we prove $0 \le (b - min) < (max - min)$.
    2.  The value $(b - min)$ is decomposed into binary bits.
    3.  Commitments to each bit are created and proven to be boolean (0 or 1) using a standard "Or-Proof" (Sigma protocol).
    4.  A consistency proof checks that the sum of bit commitments equals the commitment of $(b - min)$ (homomorphic property).
*   **Verification**: The server verifies the proof against the submitted commitment adjusted by the minimum bid: $C_{adjusted} = C_{submitted} - commit(min, 0)$.

### C. Additive Secret Sharing (Modulo $p$)
Used to distribute the bid processing.
*   **Scheme**: For a bid $b$ and a large prime $p$:
    *   $s_1, s_2 \leftarrow random \in [0, p-1]$
    *   $s_3 = (b - s_1 - s_2) \pmod p$
    *   SHARES: $\{s_1, s_2, s_3\}$ distributed to Server 1, 2, and 3 respectively.
*   **Reconstruction**: $b = (s_1 + s_2 + s_3) \pmod p$

### D. MPC Comparison Protocol
Allows servers to compare two secret-shared values $x$ and $y$ to determine if $x > y$ without reconstructing $x$ or $y$.
*   **Logic**:
    1.  Servers hold shares of $x$ and $y$.
    2.  Servers compute shares of the difference $d = x - y$ locally: $d_i = (x_i - y_i) \pmod p$.
    3.  Servers reconstruct $d$.
    4.  **Sign Check**:
        *   If $0 < d < p/2$: $d$ is positive $\Rightarrow x > y$.
        *   If $p/2 < d < p$: $d$ is negative ($p - |d|$) $\Rightarrow x < y$.
*   **Note**: This reveals the *difference* between bids in this simplified protocol, allowing determination of the max. True MPC comparison (e.g., using bitwise comparison) would hide the difference, but this implementation follows the specified arithmetic difference method.

---

## 3. Integration & Code Structure

### Client Side
*   **`client/auction.py`**: Orchestrates the registration.
    *   `register_bidder(...)`:
        1.  Generates Commitment $C$.
        2.  Constructs ZK Range Proof for $b$ (validating $min \le b \le max$).
        3.  Splits $b$ into shares $[s_1, s_2, s_3]$.
        4.  Sends package `{id, C, proof, shares}` to the system.

### Server Side
*   **`server/auction.py`**: Manages the auction lifecycle.
    *   `receive_commitment_and_proof(...)`: First, validates the ZK proof. If invalid, the bid is rejected (shares are not even processed).
    *   `receive_shares(...)`: Stores shares only for verified bidders.
    *   `compute_winner()`: Iterates through all valid bidders using `find_max_bid`.
*   **`server/mpc.py`**: Implements the arithmetic logic.
    *   `find_max_bid(...)`: Linear scan to find the max. Keeps track of `current_max` (in shares) and compares against `next_bid` (in shares) using `mpc_compare`.

### Shared Libraries
*   **`shared/commitments.py`**: ECC operations for Pedersen commitments.
*   **`shared/zkproofs.py`**: Generation and verification of bit-level range proofs.
*   **`shared/secret_sharing.py`**: Utilities for splitting and reconstructing integers modulo $p$.
