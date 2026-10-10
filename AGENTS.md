# AGENTS.md — context for AI assistants (Claude, GPT, Codex, Copilot, …)

Read this first if you are an AI assistant helping someone on team **Six_Seven**. It tells you what this
repo is, where things stand, and the rules the team has agreed. Humans: this is a good summary too.

## What this is

- **Event:** "Hack the Chip", a one-day hackathon by NYU × Annapurna Labs (the Amazon team that designs
  the AWS Trainium AI chip), on 2026-10-10.
- **Team:** Six_Seven — six people. GitHub: krishmehtagit (repo owner), Dhritii07, Smruthi01,
  manishreddy-07, Ankimax, Bhagavanmadala. Several members are not programmers (e.g. electrical
  engineering background): **explain simply, avoid jargon, keep answers short.**
- **Organisers' repo** (setup, sample projects, rules): https://github.com/yahavb/trainium-agent-labs

## What the organisers ask for

Build an **agent loop**: a language model attempts a problem → a **checker** grades the attempt → the
grade *and the reason* go back to the model → it tries again, until it solves the problem or says
honestly that it could not. Their key lesson: **the checker's feedback decides whether the loop works.**
"Wrong, off by 341%" is useless; "this term should not be there" tells the model what to change.

Required for a submission:
1. **The checker**, and the reasoning for what it accepts and rejects.
2. **An attempt log**: every attempt with its score.
3. **A one-page note**: what was run, on what, how many runs, and the spread (report rates, not one lucky run).

Scored on: correctness, results delivered, method & honesty (does the agent know when it failed?), and
the demo/write-up. Teams may pick an organiser sample project or **propose their own**, which must run on
the hardware provided and be approved by an Annapurna engineer.

## Where we are right now

- **Project chosen: VeriLoop** (Idea 6 in [`IDEAS.md`](IDEAS.md)) — the model writes Verilog for
  hardware blocks, a simulator checks it, and we measure solve rate vs. feedback quality. Status:
  **approved by an Annapurna engineer**; now building the checker (phase 3). The plan, phase by phase, is in [`TEAM.md`](TEAM.md).
  Nothing has been submitted.
- Earlier work on the organisers' kernel-agent challenge is on the branch
  [`kernel-agent-backup`](https://github.com/krishmehtagit/Six_Seven/tree/kernel-agent-backup) as a
  fallback (three checker improvements, a baseline run, and results).
- Deadlines (proposal and submission) are not known yet — check TEAM.md.

## Repo layout

| file | what it is | who maintains it |
|---|---|---|
| `TEAM.md` | the plan, phase by phase, and the requirements checklist — the single source of truth | everyone |
| `IDEAS.md` | candidate project ideas in one short format, each credited to its author | everyone |
| `idea1.md` | Dhritii07's original full write-up of idea 1 (ShapeGuard) | Dhritii07 |
| `README.md` | short intro, points here and to TEAM.md | everyone |
| `AGENTS.md` | this file | update it when the state above changes |

## Rules for any assistant working in this repo

1. **Never delete, move, or overwrite a teammate's file**, even when asked to rewrite or summarise it.
   Write your version in a separate file and link to the original. Check authorship with
   `git log --format=%an -- <file>` before removing anything.
2. **Credit authors in brackets**, e.g. "ShapeGuard (by Dhritii07)". Label your own suggestions as
   suggested by an AI assistant.
3. **Commit and push every change straight away**, after `git pull --rebase`, so all six people see the
   current state. Small commits with a clear message.
4. **Keep `TEAM.md` current** — tick checklist items, fill in deadlines, record the chosen idea. If the
   overall state changes, update "Where we are right now" above too.
5. **Never commit AWS credentials.** The event shares one temporary credential set across everyone; a
   leak gets it revoked for the whole event. They belong only in a terminal session. `.gitignore` blocks
   common credential filenames — do not work around it.
6. **Only do work that is scored.** If a task does not feed the checker, the attempt log, the one-page
   note, honesty/calibration, or the demo, say so and ask before spending time on it.
7. **Don't invent results.** Every number in the repo must come from a real run, with the number of runs
   stated. Never present a guessed cause as proven or a scripted failure as discovered.
8. **Ask before decisions that are the team's**: choosing the project, dropping work, anything
   outward-facing (making the repo public, inviting people, submitting).

## The hardware, briefly

Each person has a "seat": a Kubernetes pod (`seat-<number>`) on the organisers' cluster with one Trainium
chip (4 cores, 96 GB) and the Qwen3-8B model, which they start with `./serve.sh` inside the pod. The
model answers on `http://localhost:8000` (OpenAI-compatible API) inside the pod. Access steps are in
TEAM.md. Each person uses only their own seat. Lessons the organisers measured: keep the model's
"thinking" mode **off**, keep prompts short, put rules in the checker rather than the prompt, and never
print the target answer in feedback (the model copies it).
