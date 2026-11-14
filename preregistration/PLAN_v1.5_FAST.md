# PLAN v1.5 (FAST) — AMENDMENT: Quota-Optimized Protocol for IBM Kingston

**EZ A FÁJL AMENDMENT.** A `PLAN_v1.0.md` – `PLAN_v1.4.md`, valamint a korábbi fagyasztott fájlok
byte-ra változatlanul megmaradnak a repóban történeti rekordként.

**Indoklás:**  
Az IBM Quantum nyílt hozzáférésű fiókjának (Open Plan) havi kvótája 600 kvantum-másodperc.
A v1.4-es 4096 shotos mérés ~1065 másodpercet igényelt volna, ami meghaladta az egyetlen fiókban
elérhető keretet, és a felhő-ütemező várakozási sorában blokkolta az indítást.

A Küszöb-mérés során (`dbr1fl6jjaos73ai51pg`, `ibm_kingston`) a mért fizikai hatás nagysága:
* $P(m+1, k=8) = 0.641$
* $P(cut, k=8) = 0.216$
* Különbség: **$+0.425$ (+42.5%)**, 99%-os alsó határ: **$+0.391$**.

Egy ilyen robusztus, nagyméretű fizikai jel detektálásához a **512 shot/áramkör**
statisztikai pontossága ($\sigma \le 2.2\%$) matematikailag több mint bőségesen elegendő (> 15$\sigma$ elméleti szeparáció).

## 1. Rögzített paraméterek (v1.5 FAST)
* **Backend:** `ibm_kingston` (Heron r2)
* **Fizikai layout:** $S=125, A_1=117, A_2=124, A_3=126$ (Heron heavy-hex csomópont)
* **Áramkörök száma:** **757 db** (A teljes v1.4 paraméterrács 100%-a, nulla kihagyás, karhossz-eltérés $|\Delta| = 0$ dt)
* **Lövések száma (Shots):** **512 shot** / áramkör
* **Becsült QPU pulzusidő:** **~133.25 kvantum-másodperc**
* **Kvóta-fedezet:** Az aktív fiókban (`Hívj`) lévő 244.5 másodperces szabad keret 100%-ban fedezi a mérést, +111 másodperc biztonsági tartalékkal.
* **Csomagolás:** 4 chunk (Chunk 1: 0–250, Chunk 2: 250–500, Chunk 3: 500–750, Chunk 4: 750–757).

## 2. Döntési kapuk
A döntési logika (P1, P2, P3, anomália, Holm-korrekció $\alpha=0.01$, Wilson 99% CI)
változatlanul érvényes, 512 shotos binomiális mintavételezési modellel.
* `ANOMÁLIA`: ha az $n_3$ és $m+1$ horgonyzott ágak szignifikánsan meghaladják a tankönyvi dekoherenciát és a vágott kontrollt.
* `TEXTBOOK`: ha a csillag a vágott kontrollhoz hasonló ütemben dekoherál.
* `NINCS-VISSZATERES`: ha a jel zajszintre esik visszatérési csúcs nélkül.
