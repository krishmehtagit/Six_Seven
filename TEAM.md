# Team Six_Seven — Hack the Chip (NYU × Annapurna Labs), 2026-10-10

**Start here.** This file is the single source of truth for the team: the goal, the checklist,
where everything stands, and how to submit. Update it whenever you finish or start something — commit
and push straight away, so everyone sees it.

Upstream (the organisers' repo, read-only for us): https://github.com/yahavb/trainium-agent-labs — setup scripts, the other sample project and the gpt-oss docs live there; we only copied the kernel agent.

---

## 0. Checklist — what is done and what is left

No roles: anyone picks the next open item, says so in the team chat, and ticks it here when done.
Only work that is scored is on this list.

**Required — no valid submission without these**
- [x] **The checker**, improved: fixes A, B and C (section 4)
- [x] **Attempt log**: recorded automatically into `results/`
- [ ] **One-page note** (`SUBMISSION.md`): what we ran, how many runs, the spread — last hour

**Scored extras**
- [ ] **Measure** fixes A+B (running on seat 7) and fix C with `--repeat 5`; keep a fix only if the rate moved
- [ ] **Failure list (taxonomy)**: group the model's mistakes in `results/*.jsonl` into types, with counts — no coding
- [ ] **Calibration**: the agent says how sure it is, and says "I could not verify" when it failed
- [ ] **Demo**: one case where the model failed, our message said why, and it fixed it
- [ ] **Final run** of all 4 levels with everything in, then freeze the code
- [ ] **Submit** — deadline: ask organisers, write it here: **__:__**

**Done so far:** seat 7 set up and serving · baseline run (solved 1/4) · fix A (level 2) · fix B
(level 1) · fix C (the 1-D-tile error, levels 1 and 3) · team repo.

**Cut — not worth the time:** level 4 tiling, the gpt-oss comparison, adding new operations (softmax
etc.), on-device timing.

**Rule: whenever anything changes — code, a result, a tick on this list — commit and push it straight
away** (`git pull --rebase` first), so everyone always sees the current state.

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
| D1 | **The checker** + reasoning for what it accepts/rejects | `kernel-agent/nkibench.py`, `kernel-agent/agent.py` (`grade`), section 4 below | fixes A, B, C written up |
| D2 | **Attempt log** — every attempt with its score | `results/*.jsonl` + `results/*.log` | baseline in; A+B measurement running |
| D3 | **One-page note** — what we ran, on what, how many runs, the spread | `SUBMISSION.md` | todo |

**Scored extras** we are doing ([`ORGANISERS-CHALLENGE.md`](kernel-agent/ORGANISERS-CHALLENGE.md)):

| # | deliverable | where it lives | status |
|---|---|---|---|
| D4 | **Failure taxonomy** — wrong kernels grouped into named modes, with counts | `results/TAXONOMY.md` | todo |
| D5 | **Calibration** — agent's stated confidence vs. the truth | `kernel-agent/agent.py` + a table in section 3 | todo |
| D6 | **Demo** — a failure *and the recovery*, not just a success | `SUBMISSION.md` | todo |

How it is scored: **30%** correctness on held-back shapes · **25%** levels cleared and attempts needed ·
**25%** method & honesty (does the agent know when it failed? taxonomy) · **20%** demo & write-up.

## 3. Results — rates, not single runs

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

## 4. What we changed in the checker, and why (this is the checker deliverable)

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

**Fix C — `agent.failing_line` + `agent.one_d_cause` (levels 1 and 3).** After fix B, level 1 stopped reaching for matmul and hit the same error as level 3: `SBUF and PSUM tensors must have at least 2 dimensions`. Traced over all 39 attempts that hit it: 36 were `nl.sum(tile, axis=[0, 1])` — reducing over axis 0, the partition axis — and 3 were `shape=x.shape[1:]`, a one-element shape. The old message ("give a vector the shape (1, N)") named neither. Now every simulator error says which kernel line raised it, and for this error the line is diagnosed: a reduction over axis 0 is told never to reduce the partition axis; a sliced shape is told it is a one-element tuple. Verified on the simulator: all four reference kernels still score 1.0.

## 5. How to work — read before your first change

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
in the team chat which file you are editing. Say what changed in the commit message.

**Never commit the AWS credentials.** They are shared by the whole event; GitHub scans pushes and AWS
revokes leaked keys — which would cut off everyone. Paste them into your terminal only.

## 6. Rules of thumb the organisers measured (save yourself the day)

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
