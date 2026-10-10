# Team Six_Seven — Hack the Chip (NYU × Annapurna Labs), 2026-10-10

**Start here.** This file is the single source of truth for the team: the goal, the plan, who owns what,
where every task stands, and how to submit. Update it whenever you finish or start something — commit
and push straight away, so the other five see it.

Upstream (the organisers' repo, read-only for us): https://github.com/yahavb/trainium-agent-labs — setup scripts, the other sample project and the gpt-oss docs live there; we only copied the kernel agent.

---

## 0. Plan — only what is scored

We do **five things and nothing else**. Everything that does not feed the grade is cut (list at the bottom).

| # | task | why it matters | owner | when |
|---|---|---|---|---|
| 1 | **T5 — fix the 1-D-tile wall** (`SBUF and PSUM tensors must have at least 2 dimensions`) | one message blocks **two** levels (1 and 3) → *levels cleared* 25% + *correctness* 30% | R2 | now → 13:30 |
| 2 | **T7 — calibration**: the agent states a confidence per level and says "I could not verify" when it failed | *method & honesty* 25% — "confidently wrong is the worst behaviour" | R5 | now → 14:00 |
| 3 | **T9 — failure taxonomy**: group every wrong kernel in `results/*.jsonl` into named modes, with counts | *method & honesty*; the organisers call it "the artifact we would most want to keep". **No coding** | R4 | now → 15:30 |
| 4 | **T4 — measure every change with `--repeat 5`**, keep it only if the rate moved; one final full run | *delivered result*; the one-pager must report rates and spread | R3 (+ R1) | ongoing; final run ~15:30 |
| 5 | **T11/T12 — one-page note + demo** of a failure our feedback fixed | **required** + *demo & write-up* 20% | R6 | last hour |

**Rule for everyone: whenever you change anything — code, a result, a task status — commit and push it
straight away** (`git pull --rebase` first), so the other five always see the current state.

**Why T5 is first, from data:** after fix B, level 1 stopped reaching for matmul — the route message
worked — and then hit the **same wall as level 3** (4 of its 8 rounds in run 1). One better message for
that error could move two levels.

**Fix C (T5) — `agent.failing_line` + `agent.one_d_cause`.** Every simulator error now says which kernel line raised it. For the 1-D-tile error the line is diagnosed: a reduction over axis 0 is told axis 0 is the partition axis and must never be reduced; a sliced shape like `x.shape[1:]` is told it is a one-element tuple. Traced on all 39 attempts that hit this wall.

**Cut — do not spend time on these:** level 4 tiling (T6), the gpt-oss comparison (T10), adding new
operations (softmax etc.), on-device timing. Token instrumentation is folded into T7 as a one-line extra
(the API response already has `usage`), only if it is quick.

## 1. What we are doing, in one paragraph

We build an **agent loop** around a small model (Qwen3-8B) running on our own AWS Trainium chip: the model
writes a kernel, a **checker** grades it, and the grade *plus the reason* feed the next attempt. We picked
**Project 2, the kernel agent** — the unsolved one. Our angle is the one the organisers say wins:
**better checker feedback, measured honestly** (rates over 5 runs, not one lucky run), plus a failure
taxonomy and an agent that knows when it failed.

## 2. What we hand in

**Required** by the organisers ([README, Part 4](https://github.com/yahavb/trainium-agent-labs#part-4--the-challenge)) — no valid submission without all three:

| # | deliverable | where it lives | status |
|---|---|---|---|
| D1 | **The checker** + reasoning for what it accepts/rejects | `kernel-agent/nkibench.py`, `kernel-agent/agent.py` (`grade`), section 6 below | fixes A + B written up; T5 to add |
| D2 | **Attempt log** — every attempt with its score | `results/*.jsonl` + `results/*.log` | baseline in; A+B measurement running |
| D3 | **One-page note** — what we ran, on what, how many runs, the spread | `SUBMISSION.md` | todo (R6, last hour) |

**Scored extras** we are doing ([`ORGANISERS-CHALLENGE.md`](kernel-agent/ORGANISERS-CHALLENGE.md)):

| # | deliverable | where it lives | status |
|---|---|---|---|
| D4 | **Failure taxonomy** — wrong kernels grouped into named modes, with counts | `results/TAXONOMY.md` | todo (R4) |
| D5 | **Calibration** — agent's stated confidence vs. the truth | `kernel-agent/agent.py` + a table in section 5 | todo (R5) |
| D6 | **Demo** — a failure *and the recovery*, not just a success | `SUBMISSION.md` | todo (R6) |

How it is scored: **30%** correctness on held-back shapes · **25%** levels cleared and attempts needed ·
**25%** method & honesty (does the agent know when it failed? taxonomy) · **20%** demo & write-up.

## 3. Roles — put your name in

Team on GitHub: krishmehtagit, Dhritii07, Smruthi01, manishreddy-07, Ankimax, + 1 to come. Claim a row by writing
your name and pushing.

| role | what you own | coding? | name |
|---|---|---|---|
| R1 Lead + checker | fixes A and B, the A+B measurement, helps R2 on T5, keeps this file current | yes | Krish |
| R2 T5 owner | the 1-D-tile feedback message (`agent.py`, `enrich`) | yes | |
| R3 Measurement | `--repeat 5` runs on your own seat, the results table, the final run | a little | |
| R4 Taxonomy | read failed kernels in `results/*.jsonl`, name the modes, count them | **no** | |
| R5 Calibration | confidence per level, checked against the real score | yes | |
| R6 Write-up + demo | `SUBMISSION.md`, the demo, chases everyone for numbers | **no** | |

Everyone has their own seat (pod) and chip — run experiments on your own seat, not someone else's.

## 4. Task board

Status: `done` · `running` · `in progress` · `todo` · `blocked`. Only scored work is on here.

| ID | task | owner | status | notes |
|---|---|---|---|---|
| T0 | Seat 7 set up, Qwen3-8B serving | Krish | done | ready in ~3 min, context 8192 |
| T1 | Baseline run, all 4 levels, 1 run | Krish | done | solved 1/4; logs in `results/` |
| T2 | **Fix A**: flag element-at-a-time HBM writes (level 2) | Krish | done | see section 6 |
| T3 | **Fix B**: level-1 feedback names the route, not a list of names | Krish | done | see section 6 |
| T4 | Measure fixes A + B, levels 1 and 2, `--repeat 5` | Krish | running | seat 7, started 11:27. Level 1 run 1/5: 0.30, but the failure **moved** — matmul gone, now the 1-D-tile wall |
| T5 | 1-D-tile wall — blocks level 3 *and* (since fix B) level 1 | Krish | done, to measure | 39 failures traced: 36 = `nl.sum(..., axis=[0, 1])` (reducing the partition axis), 3 = `shape=x.shape[1:]`. New message names the line and the cause; every error now carries its line. References still 1.0. Measure after T4 finishes |
| T7 | Calibration (+ token counts if quick) | R5 | todo | |
| T9 | Failure taxonomy over all `results/*.jsonl` | R4 | todo | start now with the baseline log (76 attempts) |
| T11 | `SUBMISSION.md` one-pager + checker rationale | R6 | todo | |
| T12 | Demo: a level where an early round fails and a later round recovers *because of our message* | R6 | todo | |
| T13 | Final submission package | R6 | todo | deadline: ask organisers, write it here: **__:__** |

## 5. Results — rates, not single runs

Model Qwen3-8B on one Trainium chip, `--rounds 8 --samples 4 --context 8192`. A row with n=1 is a smoke
test, not a result. Organisers' own 5-run baseline (from their [`STATE.md`](https://github.com/yahavb/trainium-agent-labs/blob/master/STATE.md)) is the comparison point.

| level | organisers' baseline (n=5) | our baseline today (n=1) | after fixes A+B (n=5) |
|---|---|---|---|
| 1 average pooling | 0/5, always 0.30 | 0.30, not solved | run 1: 0.30 (matmul gone, now 1-D-tile wall); runs 2–5 running |
| 2 transpose | 4/5 solved | 1.00, solved on round 0 — **but the kernel wrote HBM one element at a time** (see fix A) | running |
| 3 matmul, single tile | 0/5, always 0.30 | 0.30, not solved | — |
| 4 matmul, tiled | 0/5, always 0.62 | 0.30, not solved (below their 0.62) | — |

Baseline summary (n=1): **solved 1/4** — `results/2026-10-10_krish_baseline_all.log` and `.jsonl` (76 attempts).

Important for the write-up: after fix A, level 2's rate is **expected to drop**. The old 4/5 counted
element-at-a-time kernels as solved. A lower honest number is the point, not a regression.

## 6. What we changed in the checker, and why (feeds D1)

**Fix A — `nkibench.check_issue_bound()` (level 2).** The kernel that "solved" level 2 on round 0 was
```python
for p in nl.affine_range(P):
    for i in nl.affine_range(F2):
        for j in nl.affine_range(F1):
            out[p, i * F1 + j] = sbuf[p, j, i]     # out is in HBM
```
— one HBM write per element. The transfer counter only wraps `nisa.dma_copy`, so these writes were
invisible and level 2, whose whole lesson is *the number of transfers*, scored 1.0. The new check finds
assignments (or `dst=`) into an HBM tensor, inside a loop, indexed only by scalars. A slice or `nl.ds` in
the index means a whole tile moves, which is never flagged. On level 2 it scores 0.75 (correct numbers,
half credit) and the message names the change: build the result in SBUF, then one `dma_copy`. On other
levels it is a note only — the repo's rule is that rejecting a correct kernel is worse than missing one.
Selftest: catches the real kernel above; does not flag any of the four reference kernels. Verified on the
Neuron simulator: reference level 2 → 1.0, the element-wise kernel → 0.75. The organisers listed this gap
themselves ([`STATE.md`](https://github.com/yahavb/trainium-agent-labs/blob/master/STATE.md), "Next", item 5).

**Fix B — `agent.INTENT_CALLS` and `agent.OFF_ROUTE` (level 1).** Baseline level 1 went: matmul into the
wrong buffer → invented `nc_matmul(transpose_moving=)` → invented `nisa.multiply` → invented
`nisa.scalar_mul`. Two causes: (1) told "`nki.isa` has no `multiply`", the old message listed 25 real names
alphabetically, which says what exists but not which one does the job; (2) the model was on a route —
matmul — that pooling does not need at all, and each message helped it fix the *wrong approach*. Now an
invented name that says what it wants (mul/scale/div, sum/mean/avg/pool) gets the real call for that
intent, and a level-1 kernel that uses `nc_matmul` is told to drop it and given the route — strided
`tile.ap` view → `nl.sum` over the window axes → scale by 1/(p·p) — **without the strides**, because
Project 1 measured that printing the answer makes the model copy it instead of deriving it. Verified on
the simulator: reference level 1 still → 1.0.

## 7. How to work — read before your first change

**Get on your own seat** (each person, once — full detail in the [organisers' README, Part 1](https://github.com/yahavb/trainium-agent-labs#part-1--get-onto-your-chip)):
```bash
brew install awscli kubectl                      # once
# paste the macOS/Linux credentials block from the workshop channel into THIS terminal
aws eks update-kubeconfig --name hack-hyd --region ap-south-2
kubectl get pod seat-<N>                         # want 1/1 Running
kubectl exec -it seat-<N> -- bash                # wait for root@seat-<N>:/workspace#
./serve.sh                                       # ~4 min, prints READY; leave this terminal open
```

**Edit on your laptop, run on your seat.** The pod's `/workspace` is the organisers' code and is lost if
the pod is replaced. So the code lives here, in this repo:
```bash
git clone https://github.com/krishmehtagit/Six_Seven.git && cd Six_Seven
# edit kernel-agent/*.py, then copy into your seat (the pod keeps its own path):
kubectl cp kernel-agent/nkibench.py seat-<N>:/workspace/projects/02-kernel-agent/nkibench.py -c app
kubectl cp kernel-agent/agent.py    seat-<N>:/workspace/projects/02-kernel-agent/agent.py    -c app
```

**Always prove the checker before trusting a score**, inside the seat:
```bash
cd /workspace/projects/02-kernel-agent && python nkibench.py --selftest
```

**Long runs in the background** (survives a dropped connection), with `--repeat 5` for anything we report:
```bash
nohup python agent.py --level 1 --rounds 8 --samples 4 --context 8192 --repeat 5 --log attempts-L1.jsonl > run-L1.log 2>&1 < /dev/null &
tail -f run-L1.log
```

**Bring results back into the repo** (from your laptop), named `<date>_<who>_<what>`:
```bash
kubectl cp seat-<N>:/workspace/projects/02-kernel-agent/run-L1.log        results/2026-10-10_krish_fixAB_L1.log -c app
kubectl cp seat-<N>:/workspace/projects/02-kernel-agent/attempts-L1.jsonl results/2026-10-10_krish_fixAB_L1.jsonl -c app
```
(`run*.log` and `attempts.jsonl` are gitignored on purpose — that is why results are renamed into `results/`.)

**Git.** Small commits, pull before you push (`git pull --rebase`), one person per file at a time — say
in the task board which file you are editing. Put the task ID in the commit message, e.g. `T5: name the
2-D tile fix`.

**Never commit the AWS credentials.** They are shared by the whole event; GitHub scans pushes and AWS
revokes leaked keys — which would cut off everyone. Paste them into your terminal only.

## 8. Rules of thumb the organisers measured (save yourself the day)

* **Report a rate, not your best run.** `--repeat 5`. Level 2 swings 0.5–1.0 on luck alone.
* Levels 1, 3, 4 have **zero** spread across runs — a change that moves them was your change.
* **Thinking mode off.** On: 446 s/round and score 0.00. Shorter prompt, not a bigger budget.
* **Constraints go in the checker, not the prompt.** A list of rules makes the model audit itself and
  return nothing.
* **A verdict is not an instruction.** "Off by 341%" is useless; "the sin(πx) term should not be there"
  names the fix. If the same error repeats 3 rounds, fix the message, not the prompt.
* **Never print the target answer in feedback** — the model copies it and derives nothing.
* A plausible prompt improvement once made *every* level worse. Measure before keeping anything.
* Say which numbers came from the simulator and which from the device. (All of ours: simulator.)
