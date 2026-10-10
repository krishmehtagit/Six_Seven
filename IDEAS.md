# Project ideas — Team Six_Seven

Every idea must fit the organisers' rules:
**a model attempts something → a checker grades it → the grade and the reason go back → it tries again.**
It must run on our chip, and the checker must be able to say *why* an attempt is wrong.

Add your idea at the bottom using the same format. Keep it short.

---

## Quick comparison

| # | idea | the model does | the checker | fit | risk |
|---|---|---|---|---|---|
| 1 | ShapeGuard — find where a chip kernel breaks (by Dhritii07) | picks the next test to run | compares kernel output to a trusted answer | good | the model's part is small; big scope for one day |
| 2 | Circuit designer (EE) (suggested by Claude) | picks component values for a circuit spec | a circuit simulation checks the spec | very good | we must write a small circuit solver |
| 3 | Logic designer (digital) (suggested by Claude) | writes a Boolean expression / logic for a truth table | tries every input combination | very good | may be too easy for the model |
| 4 | SQL helper (suggested by Claude) | writes a SQL query for a question | runs it and compares the result rows | good | not hardware-themed |
| 5 | Heat-rod + training (organisers' suggestion) | the organisers' solved physics project, then train the model on its own attempts | the existing physics checker | ok | training on the chip is new to us |
| **6** | **VeriLoop — the model designs chip hardware (suggested by Claude) — our best shot** | writes Verilog (the language chips are designed in) for a hardware block | simulates it on every input and names the exact signal, cycle and input that is wrong | **best** | one install (`iverilog`); levels must be tuned so the model is challenged |

---

## Idea 1 — ShapeGuard (by Dhritii07)

*Idea by Dhritii07; rewritten here in short form. Full original: [`idea1.md`](idea1.md).*

**One line:** a tool that finds the input shapes where an AI chip kernel gives wrong answers or slows
down, and shrinks each failure to the smallest example that still breaks.

**The problem:** a kernel (a small program on the chip) can pass its normal tests and still fail on an
unusual size, like a sequence length of 300 instead of 256. Engineers waste time finding which sizes are
safe and why the others fail.

**How it works:**
1. Start with one existing kernel and its trusted reference answer.
2. Generate test sizes, focusing on awkward ones (not divisible by 128, size 1, very large values).
3. Run each test and **check** the result against the reference.
4. When a test fails, **shrink** it: keep making the input smaller while it still fails.
5. The **model** reads the evidence and chooses the next most useful test.
6. Output a report: which sizes pass, which fail, the smallest failing example, and a test to keep.

**The loop:** test → check → shrink the failure → model picks the next test → repeat.

**Demo:** a kernel passes its normal tests → ShapeGuard finds a size where it fails → shrinks it to a
tiny example → show the evidence and a fix (or a regression test).

**What we hand in:** the checker (reference + tolerances), a log of every test and verdict, and a
one-page report comparing ShapeGuard with plain fixed tests.

**Notes for the team:**
- The model's job (choosing the next test) is small. Judges want *the model + checker loop* to be the
  heart of it — we should make sure the model clearly matters.
- Our harness runs kernels in the **simulator** on the CPU; real on-chip timing is not built. So the
  "where it gets slow" part is likely out of reach today. Correctness only is realistic.
- We can reuse a lot from our earlier kernel-agent work (branch `kernel-agent-backup`): the reference
  answers, awkward test sizes and the "error is in the last partial tile" detection already exist.
- Never present a guessed cause as proven, and never fake a "discovered" bug.

---

## Idea 2 — Circuit designer (uses our EE background) (suggested by Claude)

**One line:** the model designs a simple circuit to meet a spec, and a circuit simulator checks it.

**Example task:** "Design an RC low-pass filter with a cutoff of 1 kHz ±5% using standard resistor and
capacitor values." Harder levels: a voltage divider under load, an op-amp gain stage, a band-pass filter.

**How it works:**
1. The model proposes component values (e.g. R = 1.5 kΩ, C = 100 nF).
2. The **checker** simulates the circuit (a small Python solver, or ngspice) and measures the result.
3. The checker says what is wrong *and which way to go*: "cutoff is 1.06 kHz, needs 1 kHz ±5% —
   slightly too high: increase R or C."
4. The model tries again.

**Why it fits:** the checker is exact and cheap, it never needs to know the answer, and the feedback
can name the change — exactly what the organisers reward. Easy levels to hard levels, like their
projects.

**Demo:** the model gets the filter wrong on round 0, the checker says "too high, increase C", and it
lands within spec on round 2.

**Risk:** we have to write the circuit checker first (simple filters are a few lines of math; op-amps
need more).

---

## Idea 3 — Logic designer (digital) (suggested by Claude)

**One line:** the model writes logic for a truth table, and the checker tries every input.

**Example task:** "Write a Boolean expression for a 2-bit comparator / a 7-segment decoder / a
full adder."

**How it works:** the checker evaluates the model's logic on **all** input combinations and reports
exactly which rows are wrong: "inputs A=1, B=0, C=1 give 0, should give 1." The model fixes it.

**Why it fits:** the checker is perfect (it tests everything) and the feedback points to the exact row.

**Risk:** small circuits may be too easy for the model; we would need harder levels (e.g. fewest gates).

---

## Idea 4 — SQL helper (suggested by Claude)

**One line:** the model writes a database query to answer a question, and the checker runs it.

**How it works:** the checker runs the query on a small database and compares the result with the
correct rows: "you returned 12 rows, expected 9 — you included cancelled orders."

**Why it fits:** exact checker, clear feedback, easy to demo.

**Risk:** nothing to do with chips or hardware, so it may not stand out to this audience.

---

## Idea 5 — Heat-rod + training (organisers' suggestion)

**One line:** take the organisers' solved physics project (heat-equation problems) and train the model
on its own graded attempts, so it gets better instead of just retrying.

**Why it fits:** the organisers list this as "the strongest demo available here": reward climbing
across training steps, on our own chip.

**Risk:** training a model on the chip is new to all of us and may not finish in a day.

---

## Idea 6 — VeriLoop: the model designs chip hardware (suggested by Claude) — our best shot

**One line:** the small model on the chip designs digital hardware blocks in Verilog, a simulator checks
every design, and the feedback tells it exactly which signal is wrong on which clock cycle — and we
**measure** how much better feedback makes it.

**Why this could win:**
- **It speaks the judges' language.** Annapurna Labs *designs chips*. An agent that writes and verifies
  hardware is their daily work, and the top level is the building block of Trainium itself (a matrix-
  multiply cell). Our EE background fits exactly.
- **The checker is perfect and cheap.** A simulator runs the design on every input (or thousands of
  random + edge-case inputs for clocked designs) and compares it to a simple Python reference. It never
  needs to know the answer, and it can point at the exact failure.
- **We prove the organisers' main claim with a graph.** Their whole message is "the checker's feedback
  decides whether the loop works". Their own README suggests: *make the checker worse on purpose and
  measure how much slower the agent gets — the clearest evidence for the claim*. Nobody else is likely to
  do this cleanly. We run the same levels with three feedback levels, 5 runs each:
  1. **Pass/fail only** — "wrong"
  2. **Verdict** — "12 of 16 inputs wrong"
  3. **Named fix** — "on cycle 7, `count` went 9 → 0, it should go 9 → 10: the reset condition fires one
     count too early"

  and plot **solve rate vs. feedback quality**. That graph is the result.
- **Honesty built in.** The agent reports how sure it is; we check that against the simulator.

**The levels (easy → hard):**

| level | hardware block | why it is harder |
|---|---|---|
| 1 | 4-to-1 multiplexer | warm-up, proves the loop works |
| 2 | 4-bit adder with carry out | carry chain |
| 3 | 8-bit counter with enable and reset | clocked: timing matters |
| 4 | traffic-light state machine | states and transitions |
| 5 | multiply-accumulate (MAC) cell | the unit Trainium's matrix engine is built from |

**How it works:**
1. The model gets a short spec ("8-bit counter, counts up when `en` is 1, synchronous reset…").
2. It writes a Verilog module.
3. The **checker** compiles it with `iverilog` and simulates it against a Python reference on all inputs
   (combinational) or a test sequence with edge cases (clocked).
4. Feedback at the chosen level goes back; the model tries again. Every attempt is logged with its score.

**Demo (2 minutes):** level 4, the state machine. Round 0: the light goes yellow → red one cycle late. The
checker says exactly that. Round 2: fixed, all cycles pass. Then show the graph: with pass/fail-only
feedback the same model solves it 0 of 5 times; with our feedback, N of 5.

**What we hand in:** the checker (simulator + reference + feedback rules), the attempt log, the one-page
note with the solve-rate table and graph, and the demo.

**Plan for the day (fits ~5 hours):**
- Hour 1: install `iverilog` on our seats; write the checker for levels 1–2; test it on a correct and a
  deliberately broken design *before* the model is involved.
- Hour 2: connect the model (reuse the loop from our kernel-agent backup branch); levels 3–5.
- Hours 3–4: run the three feedback levels × 5 runs; fill the table.
- Last hour: graph, one-page note, demo rehearsal.

**Risks and answers:**
- *The model may already be perfect at easy levels* → that is fine; levels 3–5 are where it struggles,
  and the ablation still shows the difference.
- *Needs one install* → `apt-get install iverilog` works on our seats (checked: they have internet).
- *The hardware rule* → the model runs on our Trainium chip; the checker runs on the CPU, exactly like
  both organiser sample projects.

**Pitch to the Annapurna engineer, in one sentence:**
> "A small model on your chip designs chip hardware, a simulator grades every design down to the exact
> signal and cycle, and we measure how much the quality of that feedback changes the success rate."

---

## Add your idea

```
## Idea N — Name (by your-name)

**One line:**
**How it works:** (what the model does, what the checker checks, what the feedback says)
**Why it fits:**
**Demo:**
**Risk:**
```
