# Six_Seven — Hack the Chip (NYU × Annapurna Labs)

An agent that writes NKI kernels for AWS Trainium, with a checker whose feedback tells the model *what
to change*, measured over repeated runs.

**Team: start with [`TEAM.md`](TEAM.md)** — plan, roles, task board, results, and how to work.

| folder | what is in it |
|---|---|
| [`kernel-agent/`](kernel-agent/) | the agent (`agent.py`), the checker (`nkibench.py`), the reference kernels, and the organisers' two docs for this project |
| [`results/`](results/) | every run we report: the log and the attempt-by-attempt JSONL, named `<date>_<who>_<what>` |

Built on the organisers' repo, [yahavb/trainium-agent-labs](https://github.com/yahavb/trainium-agent-labs),
which has the cluster setup, the other sample project and the gpt-oss endpoint docs. Model: Qwen3-8B on
one Trainium chip. All numbers come from the Neuron **simulator** (`nki.simulate`), not on-device timing.
