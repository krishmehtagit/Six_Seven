# Team Six_Seven — Hack the Chip (NYU × Annapurna Labs), 2026-10-10

**Start here.** One page: our idea, what the organisers require, and where we are.
Whenever anything changes, commit and push straight away (`git pull --rebase` first) so everyone sees it.

## Our idea: VeriLoop

**The small model on our Trainium chip designs digital hardware in Verilog. A simulator checks every
design and tells the model exactly which signal is wrong on which clock cycle. We measure how much the
quality of that feedback changes the success rate.** Full write-up: Idea 6 in [`IDEAS.md`](IDEAS.md).

**The levels, easy → hard.** 1–3 are the core; 4–8 are the harder levels, where small models struggle and
the feedback should matter most — that is what makes the graph meaningful.

| level | hardware block | what makes it hard | core / harder |
|---|---|---|---|
| 1 | 4-to-1 multiplexer | warm-up: proves the loop works | core |
| 2 | 4-bit adder with carry out | the carry chain | core |
| 3 | 8-bit counter with enable and reset | clocked: timing and reset matter | core |
| 4 | traffic-light state machine | states, transitions, timing | harder |
| 5 | multiply-accumulate (MAC) cell | multiply + add + keep a running sum; the unit Trainium's matrix engine is built from | harder |
| 6 | FIFO buffer (4 entries) | full/empty flags, read and write in the same cycle | harder |
| 7 | 2×2 systolic array | four MAC cells passing data to their neighbours each cycle — a mini version of Trainium's matrix engine | harder |
| 8 | pipelined MAC (2 stages) | the answer arrives one cycle later; the model must keep the stages in step | harder |

Write each harder level's spec and test bench the same way as levels 1–3. If a level turns out too easy
(solved on round 0 every time) or too hard (never past 0.0), note it and move on — both are results.

The experiment: same levels, **three feedback levels**, 5 runs each →
**A** pass/fail only · **B** "12 of 16 inputs wrong" · **C** "cycle 7: `count` went 9 → 0, should be 9 → 10".
The result is one table and one graph: **solve rate vs. feedback quality**.

### Who does what — in one round

| who | writes | what it does |
|---|---|---|
| **We (the team)** | **Python**: the checker and the loop | sets the task, tests the model's design, writes the feedback, logs everything |
| **The model** (Qwen3-8B on our Trainium chip) | **Verilog**: the hardware design | reads the task, designs the circuit, fixes it when told what is wrong |
| **The simulator** (`iverilog`, a ready-made tool) | — | runs the Verilog like a real circuit |

1. **Input to the model:** a short spec we write — e.g. *"8-bit counter: counts up by 1 each clock when
   `en` = 1; goes to 0 when `reset` = 1."* (from round 2 on, plus the checker's feedback)
2. **Output of the model:** a Verilog module (~10 lines).
3. **Our checker** simulates it, compares with the correct behaviour (a Python reference), and outputs a
   **score** (e.g. 0.6) and **feedback** (e.g. "cycle 7: `count` went 9 → 0, should be 9 → 10").
4. The feedback goes back to the model; repeat up to 8 rounds.

**What we get at the end:** the attempt log (every design, score and feedback), the results table and
graph (solve rate vs. feedback quality), and the demo case.

## Plan — phase by phase

Times are a guide; fix them once we know the deadlines. Tick items as they are done, and push.

### 1. Planning — done
- [x] Ideas collected in `IDEAS.md`; the team picked **VeriLoop**
- [x] Fits the rules: the model runs on our Trainium chip; the checker (a Verilog simulator) runs on the
      CPU, exactly like both organiser sample projects

### 2. Approval — ✅ done: approved by an Annapurna engineer

**Who goes:** two people — one who explains, one who takes notes. Bring a laptop with this page open.

**How we pitch it (about 1 minute):**

1. **Open with one sentence:**
   > "A small model on your chip designs chip hardware, a simulator grades every design down to the exact
   > signal and clock cycle, and we measure how much the quality of that feedback changes the success rate."
2. **The loop, in plain words:** "The model writes a Verilog module from a short spec. We simulate it
   against a Python reference on every input. The checker says what is wrong — for example 'on cycle 7 the
   counter wrapped to 0 instead of going to 10' — and the model tries again. Every attempt is logged."
3. **Why it fits your rules:** "The model runs on our seat's Trainium chip. The checker runs on the CPU,
   like the heat-rod and kernel projects. We hand in the checker, the attempt log and a one-page note."
4. **Why it matters to Annapurna:** "It is your daily work — designing and verifying hardware — and level 5
   is a multiply-accumulate cell, the unit your matrix engine is built from."
5. **The result we promise:** "Your README suggests making the checker worse on purpose and measuring the
   slowdown. We do exactly that: three feedback levels, five runs each, and a graph of solve rate versus
   feedback quality. We report rates and spread, not one lucky run."
6. **Ask them directly:** "Does this fit in a day? Is anything here against the rules?"

**Questions they may ask, and our answers:**

| they ask | we answer |
|---|---|
| "Isn't the checker on the CPU, not the chip?" | Yes — the *model* runs on the chip, the checker on the CPU, same as both of your sample projects. |
| "What if the model solves everything first try?" | Levels 3–5 are clocked designs where small models struggle; and if it does, the feedback comparison is still measured on the levels where it fails. We will report it honestly either way. |
| "How do you know the checker is right?" | We test it on a correct design and on deliberately broken ones *before* the model is involved, and ship those tests. |
| "Why not just use a bigger model?" | The question is whether the *loop* makes a small model succeed — that is your challenge statement. |
| "Can you finish in time?" | Levels 1–3 and the A/B/C comparison are the core; levels 4–8 are harder levels we add once the core works. One install (`iverilog`), already checked on our seat. |

**Also ask them:**
- [ ] The **proposal deadline** and the **submission deadline** — write them in the requirements list below
- [ ] **How and where** to submit (a repo link? a form? a presentation slot?)
- [ ] Whether our repo must be **public** for judging

**Outcome:**
- [x] **Approved** → start phase 3 at once
- [ ] Changes requested → write them here, adjust, and go back if needed
- [ ] Not approved → fall back to the kernel-agent work on branch `kernel-agent-backup`

### 3. Build the checker first (~1 hour) — ▶️ NOW

**👉 Specific tasks, file paths and who-is-doing-what are in [`TASKS.md`](TASKS.md). Pick one there.**
- [ ] Install `iverilog` on each seat that runs experiments (`apt-get install -y iverilog`)
- [ ] For levels 1–3: the spec (3–5 lines each), a Python reference model, and a test bench that
      tries every input (combinational) or a test sequence with edge cases (clocked: reset, enable off,
      wrap-around)
- [ ] Feedback at all three levels — A, B, C — from the same simulation
- [ ] **Prove the checker before the model touches it:** a correct design must pass, and at least 3
      deliberately broken designs per level must fail with the right message
- [ ] **Sanity-check rule:** a feedback message never contains the full answer (the organisers measured
      that the model just copies it)

### 4. Connect the model (~1 hour)
- [ ] One attempt end to end on level 1: spec → model → Verilog → checker → score
- [ ] The loop: up to 8 rounds, 4 attempts per round, feedback level chosen by a flag; reuse the loop
      code from `kernel-agent-backup` (`agent.py`) where it helps
- [ ] Log every attempt: level, round, feedback level, the Verilog, score, the feedback sent
- [ ] Thinking mode **off**, prompts short (organisers measured both)
- [ ] Once levels 1–3 work end to end, add the **harder levels 4–8** — spec, Python reference and test
      bench for each, tested on a correct and a deliberately broken design first, just like the core.
      Suggested order: 4 state machine → 5 MAC → 6 FIFO → 7 systolic array → 8 pipelined MAC
- [ ] Several people can write harder levels at the same time — one level per person, one file each

### 5. Measure (~1.5 hours)
- [ ] For each level × feedback level A / B / C: **5 runs**; record solved-out-of-5, rounds needed, spread
- [ ] Fill the results table below; make the graph (solve rate vs. feedback level)
- [ ] Calibration: the agent says "solved" or "could not verify" — check every claim against the simulator
- [ ] Pick the demo case: a failure on an early round that feedback C fixes

### 6. Write-up, demo, submit (last hour)
- [ ] `SUBMISSION.md` — one page: what we ran, on what, how many runs, the spread, the graph, limits
- [ ] The checker write-up: what it accepts and rejects, and why
- [ ] Demo rehearsed once (2 minutes: the failure → the feedback → the fix → the graph)
- [ ] Final check of the requirements list below, then submit

## Findings so far (real runs, seat 7)

- **The full loop works on the chip:** spec → Qwen3-8B → Verilog → simulator → score + feedback.
- **Easy blocks are solved on the first try:** an 8-bit counter and a 4-bit adder, 4 of 4 attempts correct
  on round 0 (n=1 run each). So levels 1–3 will not show a feedback difference — **the experiment lives in
  the harder levels 4–8.** Make their specs precise and their tests thorough.
- **Sampling:** at temperature 0.7 the model gave 4 identical answers out of 4; at 1.0 they differ, so the
  agent uses 1.0. On a very easy task it still repeats itself, which is expected.
- **Level 4 (traffic light) is hard enough:** on round 0 all 4 attempts failed (scores 0.61–0.66). This
  is the first level where feedback can make a difference. Experiment running on seat 7: A/B/C × 5
  runs, 6 rounds each.
- **It is slow:** the model writes ~500–700 tokens per design at ~7 tokens/s, so a round takes ~100 s and
  one seat needs ~2 h for one hard level. **More seats = faster results** — every teammate who starts
  their seat (SERVER.md) can run part of the experiment with `run_experiment.py --tag <you>`.
- **Never send `seed` to the model server** — it crashed seat 7's server (restarted, back up).

## Results (fill in from real runs only)

| level | A: pass/fail (solved / 5) | B: verdict (solved / 5) | C: named fix (solved / 5) |
|---|---|---|---|
| 1 mux | | | |
| 2 adder | | | |
| 3 counter | | | |
| 4 state machine | | | |
| 5 MAC cell | | | |
| 6 FIFO buffer | | | |
| 7 2×2 systolic array | | | |
| 8 pipelined MAC | | | |

## What the organisers require for our own project

- [ ] **It runs on the hardware they gave us** (our seats: one Trainium chip each, with the Qwen3-8B model)
- [x] **Approved by an Annapurna engineer**
- [ ] **A checker**: something that grades each attempt, plus our reasoning for what it accepts and rejects
- [ ] **An attempt log**: every attempt with its score
- [ ] **A one-page note**: what we ran, on what, how many runs, and the spread
- [ ] **Submit** — deadline: **__:__**

The pattern they want: a model attempts something → a checker grades it → the grade *and the reason*
go back to the model → it tries again, until it solves the problem or says honestly that it could not.

## Where we are

- **VeriLoop is approved** by an Annapurna engineer. Now: phase 3, build the checker.
- Seat 7 is set up and the model is running on it.
- Team repo: this one. Members: krishmehtagit, Dhritii07, Smruthi01, manishreddy-07, Ankimax, Bhagavanmadala.
- Earlier work on the organisers' kernel-agent challenge is kept on the branch
  [`kernel-agent-backup`](https://github.com/krishmehtagit/Six_Seven/tree/kernel-agent-backup), in case we need a fallback.

## Getting on your seat (the server)

Full step-by-step guide — install, connect, start the model, install the simulator, copy code over,
run long jobs, fix common errors — is in **[`SERVER.md`](SERVER.md)**. Add your seat number there.

**Never commit the AWS credentials.** They are shared by the whole event.
