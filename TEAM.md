# Team Six_Seven — Hack the Chip (NYU × Annapurna Labs), 2026-10-10

**Start here.** One page: our idea, what the organisers require, and where we are.
Whenever anything changes, commit and push straight away (`git pull --rebase` first) so everyone sees it.

## Our idea

**To be decided by the team.** Candidates are in [`IDEAS.md`](IDEAS.md). Write the chosen one here in 2–3 lines once agreed.

## Plan — phase by phase

Times are rough until we know the deadlines. Tick a phase when it is done.

**1. Planning (now)**
- [ ] Everyone pitches ideas; pick **one**
- [ ] Check it fits: runs on our chip, uses the model, and has a **checker** — a cheap, exact way to
      say if an attempt is right and *why* it is wrong
- [ ] Write the idea in 2–3 lines under "Our idea" above

**2. Approval**
- [ ] Pitch it to an Annapurna engineer and get a yes (before the proposal deadline)
- [ ] Ask for the submission deadline; write both times below

**3. Build**
- [ ] The **checker** first, tested on known-good and known-bad answers *before* the model is involved
- [ ] One model attempt end to end
- [ ] The loop: attempt → checker → feedback → retry, logging every attempt with its score

**4. Measure**
- [ ] Run it several times (not once) and record the success rate and spread
- [ ] Improve the checker's feedback where the model gets stuck; re-measure; keep only what helps

**5. Write-up and demo**
- [ ] One-page note: what we ran, on what, how many runs, the spread
- [ ] Demo: one case where the model failed, the feedback said why, and it recovered

**6. Submit**
- [ ] Final check of the requirements list, then submit

## What the organisers require for our own project

- [ ] **It runs on the hardware they gave us** (our seats: one Trainium chip each, with the Qwen3-8B model)
- [ ] **Approved by an Annapurna engineer** before the proposal deadline — originally 11:30, postponed; new time: **__:__**
- [ ] **A checker**: something that grades each attempt, plus our reasoning for what it accepts and rejects
- [ ] **An attempt log**: every attempt with its score
- [ ] **A one-page note**: what we ran, on what, how many runs, and the spread
- [ ] **Submit** — deadline: **__:__**

The pattern they want: a model attempts something → a checker grades it → the grade *and the reason*
go back to the model → it tries again, until it solves the problem or says honestly that it could not.

## Where we are

- Seat 7 is set up and the model is running on it.
- Team repo: this one. Members: krishmehtagit, Dhritii07, Smruthi01, manishreddy-07, Ankimax, Bhagavanmadala.
- Earlier work on the organisers' kernel-agent challenge is kept on the branch
  [`kernel-agent-backup`](https://github.com/krishmehtagit/Six_Seven/tree/kernel-agent-backup), in case we need a fallback.

## Getting on your seat (each person, once)

```bash
brew install awscli kubectl
# paste the macOS/Linux credentials block from the workshop channel into THIS terminal
aws eks update-kubeconfig --name hack-hyd --region ap-south-2
kubectl get pod seat-<N>                 # want 1/1 Running
kubectl exec -it seat-<N> -- bash        # wait for root@seat-<N>:/workspace#
./serve.sh                               # ~4 min, prints READY; leave this terminal open
```

**Never commit the AWS credentials.** They are shared by the whole event.
