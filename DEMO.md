# VeriLoop — 2-minute demo script

> **DRAFT — the live case (⏳) is picked from the real runs when they finish: a run where an early round
> fails and a later round passes because of the feedback.**

## 0:00 — the one-line pitch (say it)

> "A small model on your chip designs chip hardware. A simulator grades every design down to the exact
> signal and clock cycle. We measured how much the *quality* of that feedback changes whether it succeeds."

## 0:15 — the loop (show `TEAM.md` → "Who does what", or draw it)

spec → **Qwen3-8B on Trainium** writes Verilog → **simulator** checks every test → score + feedback → back to
the model. The checker is the only judge: the agent says `SOLVED` only when every test passed.

## 0:35 — one real failure and recovery ⏳

Open the attempt log for the chosen run (`results/<file>_attempts.jsonl`, run id ⏳) and show, round by round:

1. **Round 0** — the model's design, score ⏳, and the exact feedback C it got back, e.g.
   `cycle 6: light = YELLOW (2), expected GREEN (1)  <-- first wrong cycle`
2. **Round ⏳** — the fixed line in the design, and `SOLVED -- verified by the checker on every test`.

Say: *"It did not get the answer from us — the checker never prints the whole table. It got the cycle."*

## 1:05 — the result (show `results/graph.png`)

- Easy blocks (mux, adder, counter): solved on the first try with **any** feedback — 72/72.
- Hard blocks (traffic light, MAC, FIFO): ⏳ the A / B / C comparison, as solved / runs.

## 1:30 — what we learned (pick two)

- Feedback quality ⏳ (the headline from the graph).
- The model **goes in circles** without being told it repeated itself — identical design 6 rounds running.
- "8 runs" can be **2 runs**: the model is nearly deterministic, so we fingerprinted every design to prove
  our runs are independent.
- The model's own confidence vs the checker ⏳ (calibration).

## 1:50 — close

> "Everything — the checker, every attempt, every number — is in the repo, and `selftest.py` proves each
> level before the model ever sees it."

## Backup if the live part fails

Show `results/graph.png` and the round-by-round story from the log file in a text editor — no live model
needed.
