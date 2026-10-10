# Team Six_Seven — Hack the Chip (NYU × Annapurna Labs), 2026-10-10

**Start here.** This file is the single source of truth for the team: the goal, the plan, who owns what,
where every task stands, and how to submit. Update it whenever you finish or start something — commit
and push straight away, so the other five see it.

Upstream (the organisers' repo, read-only for us): https://github.com/yahavb/trainium-agent-labs — setup scripts, the other sample project and the gpt-oss docs live there; we only copied the kernel agent.

---

## 0. Plan for the day

Times after 12:00 are **tentative** until we know the submission deadline (T13). Fill it in when you hear it.

| when | phase | who | done means |
|---|---|---|---|
| ~11:40 – 12:30 | **Join + set up.** Accept the GitHub invite, claim a role in section 3, get on your own seat (section 7), start the model | everyone | your name is in section 3 and your seat prints `READY` |
| 12:00 – 14:00 | **Build.** R2 fixes the 1-D-tile wall (T5, now the top priority, see below) then level 4; R5 adds calibration + token counts; R4 starts the taxonomy from `results/`; R1 finishes fix A+B measurement | by role | each change merged *and* passes `python nkibench.py --selftest` |
| 14:00 – 15:30 | **Measure.** Every change gets `--repeat 5`; R3 fills section 5. Keep a change only if the rate moved | R3 + owners | section 5 has a number for every change |
| 15:30 – 16:30 | **Final run + freeze.** One `--all --repeat 5` run with everything merged; no code changes after it | R3 | final row in section 5, logs in `results/` |
| last hour | **Write-up + demo.** `SUBMISSION.md`, taxonomy table, demo of a failure recovered by our feedback; rehearse once | R6 + R4 | all six deliverables in section 2 marked done |

**Rule for everyone: whenever you change anything — code, a result, a task status — commit and push it
straight away** (`git pull --rebase` first), so the other five always see the current state.

**Top priority right now, from data:** after fix B, level 1 stopped reaching for matmul — the route
message worked — and then hit the **same wall as level 3**: `SBUF and PSUM tensors must have at least 2
dimensions` (4 of its 8 rounds in run 1). One better message for that error could move two levels. That is T5.

## 1. What we are doing, in one paragraph

We build an **agent loop** around a small model (Qwen3-8B) running on our own AWS Trainium chip: the model
writes a kernel, a **checker** grades it, and the grade *plus the reason* feed the next attempt. We picked
**Project 2, the kernel agent** — the unsolved one. Our angle is the one the organisers say wins:
**better checker feedback, measured honestly** (rates over 5 runs, not one lucky run), plus a failure
taxonomy and an agent that knows when it failed.

## 2. What we hand in (the judged deliverables)

From the [organisers' README, Part 4](https://github.com/yahavb/trainium-agent-labs#part-4--the-challenge), and [`kernel-agent/ORGANISERS-CHALLENGE.md`](kernel-agent/ORGANISERS-CHALLENGE.md):

| # | deliverable | where it lives | owner | status |
|---|---|---|---|---|
| D1 | **The checker** + reasoning for what it accepts/rejects | `kernel-agent/nkibench.py`, `kernel-agent/agent.py` (`grade`), section 6 below | | in progress |
| D2 | **Attempt log** — every attempt with its score | `results/*.jsonl` + `results/*.log` | | baseline in |
| D3 | **One-page note** — what we ran, on what, how many runs, the spread | `SUBMISSION.md` (to write) | | todo |
| D4 | **Failure taxonomy** — every wrong kernel, grouped into named modes, with counts | `results/TAXONOMY.md` (to write) | | todo |
| D5 | **Token instrumentation** — input tokens per attempt, what they were spent on | `results/` | | todo |
| D6 | **Demo** — show a failure *and the recovery*, not just a success | | | todo |

How it is scored (kernel challenge): **30%** correctness on held-back shapes · **25%** levels cleared and
attempts needed · **25%** method & honesty (does the agent know when it failed? taxonomy, token
instrumentation) · **20%** demo & write-up (can they reproduce it?).

## 3. Roles (6 people) — put your name in

| role | what you own | name |
|---|---|---|
| R1 Checker — levels 1–2 | feedback messages for pooling and transpose (fixes A and B below) | Krish |
| R2 Checker — levels 3–4 | the matmul walls: 1-D tiles, reshape-instead-of-slice, partition > 128 | |
| R3 Measurement | runs every change with `--repeat 5`, keeps the results table (section 5) honest | |
| R4 Failure taxonomy | reads every failed kernel in the attempt logs, names the failure modes, counts them — **no coding needed** | |
| R5 Agent features | calibration (agent outputs a confidence and is right about it) + token instrumentation | |
| R6 Write-up & demo | `SUBMISSION.md`, the demo script, the final package; chases everyone for numbers | |

Everyone has their own seat (pod) and chip — run experiments on your own seat, not someone else's.

## 4. Task board

Status: `done` · `running` · `in progress` · `todo` · `blocked`. Add rows freely; keep IDs stable.

| ID | task | owner | status | notes |
|---|---|---|---|---|
| T0 | Seat 7 set up, Qwen3-8B serving | Krish | done | ready in ~3 min, context 8192 |
| T1 | Baseline run, all 4 levels, 1 run | Krish | done | solved 1/4; logs in `results/` |
| T2 | **Fix A**: flag element-at-a-time HBM writes (level 2) | Krish | done | see section 6 |
| T3 | **Fix B**: level-1 feedback names the route, not a list of names | Krish | done | see section 6 |
| T4 | Measure fixes A + B, levels 1 and 2, `--repeat 5` | Krish | running | seat 7, started 11:27. Level 1 run 1/5: 0.30, but the failure **moved** — matmul gone, now the 1-D-tile wall (see section 0) |
| T5 | **TOP PRIORITY.** 1-D-tile wall: "SBUF and PSUM tensors must have at least 2 dimensions" — blocks level 3 *and* (since fix B) level 1 | R2 | todo | the organisers measured this wall as identical every run, so a fix is cleanly attributable |
| T6 | Level 4 wall: `dma_copy dst partition dimension 256 exceeds maximum 128` | R2 | todo | best 0.62 (passes 1 of 4 shapes) |
| T7 | Calibration: agent prints a confidence per level and we check it against the truth | R5 | todo | "confidently wrong" is the worst behaviour in the rubric |
| T8 | Token instrumentation per attempt | R5 | todo | prompt tokens are in the API response `usage` field |
| T9 | Failure taxonomy over all `results/*.jsonl` | R4 | todo | start now with the baseline log |
| T10 | Compare against shared `gpt-oss-20b` (`--samples 1 --terse 1`) | R3 | blocked | needs the endpoint URL from the organisers |
| T11 | `SUBMISSION.md` one-pager + checker rationale | R6 | todo | |
| T12 | Demo: one level where round 0 fails and a later round recovers *because of our message* | R6 | todo | |
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
