"""Keringési állapotok — a terv saját definíciója (fluxustól független).

Cirkulációs kvantumszám: a hurokáram L sajátértéke (Φ=0 felbontásban).
Három csomópontra:

    |m=+1> = (1, ω, ω²)/√3      ω = e^{2πi/3}   (forgó, CCW)
    |m=−1> = (1, ω², ω)/√3                        (ellenforgó)
    |m= 0> = (1, 1, 1)/√3                         (nem forgó)

Azonos populációk (1/3-1/3-1/3) — a "sötétállapot-teszt" tisztán a fázisok
(keringés) hatását méri. A prep gerjesztés-megőrző, fix felépítésű
sablon (MINDEN karban azonos kapuszerkezet):
    X(R1) + U_XY(R1,R2; t1,p1) + U_XY(R2,R3; t2,p2)
(1 db 1-qubites X + 2 kétqubites kapu — a kaputilus-egyeztetést nem bontja meg).

Dekompozíció: v = (v0,v1,v2), |v|=1, basis (|R1>,|R2>,|R3>) 1-excitációs.
    t1 = acos(|v0|);                 # U(q1,q2) |10> -> cos t1|10> - i e^{ip1} sin t1|01>
    b  = sqrt(|v1|^2+|v2|^2);
    t2 = acos(|v1|/b);               # U(q2,q3) |01> -> cos t2|01> - i e^{ip2} sin t2|10>
    p1 = arg(v1) + pi/2;             # -i e^{ip1} sin t1 = e^{i arg v1}|v1|
    p2 = arg(v2) - arg(v1) + pi/2;   # v2 = -s1 s2 e^{i(p1+p2)}
"""
from __future__ import annotations

import math
import numpy as np

SQRT3 = math.sqrt(3.0)
OMEGA = np.exp(2j * np.pi / 3)

CIRCULATION = {
    +1: np.array([1.0, OMEGA, OMEGA**2], dtype=complex) / SQRT3,
    -1: np.array([1.0, OMEGA**2, OMEGA], dtype=complex) / SQRT3,
    0:  np.array([1.0, 1.0, 1.0], dtype=complex) / SQRT3,
}


def decompose(v: np.ndarray):
    v = np.asarray(v, dtype=complex)
    assert v.shape == (3,) and abs(np.linalg.norm(v) - 1.0) < 1e-9
    t1 = math.acos(min(max(abs(v[0]), -1.0), 1.0))
    b = math.hypot(abs(v[1]), abs(v[2]))
    t2 = math.acos(min(max(abs(v[1]) / b, -1.0), 1.0)) if b > 1e-12 else 0.0
    a1 = math.atan2(v[1].imag, v[1].real)
    a2 = math.atan2(v[2].imag, v[2].real)
    p1 = a1 + math.pi / 2
    # v2 = -s1 s2 e^{i(p1 - p2)}  =>  arg v2 = p1 - p2 + pi  =>  p2 = a1 + pi/2 - a2 - pi
    p2 = a2 - a1 + math.pi / 2
    return t1, p1, t2, p2


def prep_angles(m: int):
    if m not in CIRCULATION:
        raise ValueError(m)
    return decompose(CIRCULATION[m])


if __name__ == "__main__":
    for m, v in CIRCULATION.items():
        t1, p1, t2, p2 = prep_angles(m)
        print(f"m={m:+d}  t1={t1:.6f} p1={p1:.6f}  t2={t2:.6f} p2={p2:.6f}  |v|^2={np.abs(v**2).sum():.4f}")
    # köráram-ellenőrzés (Φ=0 hurokáram-operátor)
    edges = [(0, 1), (1, 2), (2, 0)]
    def bond_current(i, j):
        J = np.zeros((3, 3), complex)
        J[i, j] = -1j  # -i t_ij, tij = -1 (Φ=0)
        J[j, i] = 1j
        return J
    for m, v in CIRCULATION.items():
        I = [float(np.vdot(v, bond_current(i, j) @ v).real) for i, j in edges]
        print(f"m={m:+d}  hurokáram-élek: {[round(x,4) for x in I]}")
