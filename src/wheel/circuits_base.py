"""Közös alapok a Kerék-menet áramköreihez (bitek, él-mátrix)."""
from __future__ import annotations

import math
import numpy as np

Q_S, Q_R1, Q_R2, Q_R3 = 0, 1, 2, 3
N_QUBITS = 4

def edge_matrix(theta: float, phi_f: float, reverse: bool = False) -> np.ndarray:
    """PSWAP-szerű él: U[1,1]=U[2,2]=cosθ; U[1,2] = -i sinθ e^{-iφ}; U[2,1] = -i sinθ e^{+iφ}.

    A reverse=True a φ előjelét váltja (a 3-ik él fázis-záródása).
    XY-család: bármely (θ, φ) pontosan 2 CX-ból szintetizálható.
    """
    c = math.cos(theta)
    s = math.sin(theta)
    ph = -phi_f if reverse else phi_f
    U = np.eye(4, dtype=complex)
    U[1, 1] = c
    U[2, 2] = c
    U[1, 2] = -1j * s * np.exp(-1j * ph)
    U[2, 1] = -1j * s * np.exp(1j * ph)
    return U
