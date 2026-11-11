# ERRATA — preregistration/PLAN_v1.0.md

**Dátum:** 2026-11-11 · **Forrás:** Control Agent auditja (0. fázis lezárása után) · **Érintett fájl:** `PLAN_v1.0.md` · **Hatás:** tartalmi (szöveges), a döntési szabályokat NEM érinti

## A hiba leírása (a Control Agent jelentése szerint)

A `PLAN_v1.0.md` **195. sora** egyszavas eltérést tartalmaz az eredeti
kísérletterv-szöveghez képest. A kérdéses sor teljes tartalma:

```
countsból történik.
```

— ez a dokumentum végén álló utolsó előtti mondat (a „A QPU-beküldést nem az
agent végzi …" kezdetű bekezdés) zárómondata.

## Amit ITT dokumentálunk (és amit nem)

- **A `PLAN_v1.0.md` fájl NEM került módosításra.** A befagyasztott/hash-elt
  állapot érintetlen:
  - `preregistration/PLAN_v1.0.md` SHA-256:
    `12b22f18c468f05ab5ca10ed0bbb0819ed85e21564f3a3780b51c25508e38775`
    (a `frozen_params.sha256`-ban rögzítve — egyezik),
  - `preregistration/frozen_params.json` SHA-256:
    `e1d7a78888c531ba8ae7e5f84ed090649f5156774eabd763c8772d5d02d09429`
    (változatlan).
- **A pontos eredeti szóalakot a repóból nem lehet rekonstruálni** — a repo nem
  tartalmazza az eredeti forrásszöveget (a hiba éppen egy innen-oda való
  másolás során keletkezett). A Control Agent rendelkezik az eredeti
  példánnyal; a pontos szóalakot ő tudja megadni.
- **Helyesbítés a jövőre:** a javítás KIZÁRÓLAG verziószámozott, „amended"
  jelölésű kiegészítéssel történhet (pl. `PLAN_v1.1.md`, amelynek a fejléce
  „amended" jelölést kap, és amely tételesen felsorolja az eltéréseket).
  A `PLAN_v1.0.md`-t retroaktívan átírni TILOS — a preregisztráció hitelessége
  emiatt sérülne.
- **Tartalmi hatás:** a 195. sor kizárólag a beküldési folyamatot leíró
  mondat része; a döntési szabályt, a tűréseket, a P1/P2/P3 feltételeket, az
  anomália-definíciót NEM érinti. A `frozen_params.json`-ba rögzített
  paraméterek és az elemző logika független ettől a hibától.

## Javasolt teendő

1. A Control Agent (vagy a tulajdonos) adja meg a pontos eredeti szóalakot.
2. Jóváhagyás után készüljön `PLAN_v1.1.md` „amended" jelöléssel, külön
   commitban; a `PLAN_v1.0.md` és a hozzá tartozó hash minden esetben
   változatlan marad (a git-történet igazolja).
