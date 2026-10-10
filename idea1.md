After looking at AWS's own engineering priorities, I'd change my recommendation significantly.

I would not build another autonomous kernel-writing agent. I'd build something that helps AWS engineers discover why an optimization works, why it fails, and whether it will actually save money in production.

There is a real opportunity here: AWS has already been developing agentic tools for writing, debugging, profiling, and optimizing NKI kernels. Its own documentation emphasizes data movement, compute utilization, execution overlap, and memory bottlenecks. A generic "LLM writes a faster kernel" project risks duplicating work that AWS is already doing.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://aws.amazon.com\&sz=32)

Artificial Intelligence

+2



The question I'd ask instead is: What expensive engineering decision does AWS still need to make that an agent could learn to make better?

## The project I'd actually bet on: ShapeGuard

[Advanced Reliability Verification  | Siemens](https://images.openai.com/static-rsc-4/wLxRudty4FEWVDb2wyJw-NTN6D67tiRd57MhrqO--EGdUyB_sBtfU1zGG4SU9yiI1YAS350L1VVq0ZNB5R_psZWVGjjMEp4wtopwrQNd4SjZclIw-DF7MtbQDxJu4IoegDuPLhrjQ8KbSH31eF-qKTsXtBd4E3uAcWy2pFF_gik?purpose=inline)

[resources.sw.siemens.com](https://resources.sw.siemens.com/en-US/fact-sheet-calibre-perc/)

My top recommendation

# ShapeGuard: Discover the breaking points of AI kernels before production.

A hardware-verified agent that maps where a Trainium kernel works, where it breaks, and where it becomes unexpectedly slow.

The core insight: Don't ask the model to write a better kernel. Ask it to discover the exact conditions under which a kernel can be trusted.

Given a kernel, ShapeGuard generates test cases, executes them on Trainium, checks correctness, diagnoses failures, searches for minimal reproductions, and builds a map of the kernel's verified operating range.

### Why this could matter to Amazon

Imagine an AWS customer deploys a model whose tensor dimensions vary with prompt length, batch size, and workload. A custom kernel passes the developer's original tests but fails on an unusual sequence length—or compiles successfully yet becomes dramatically slower for certain shapes.

A developer wants answers to questions like:

- Which input shapes and data types are actually supported?
- What is the smallest input that triggers a failure?
- Is this a compiler limitation, a numerical issue, or a kernel bug?
- At which input sizes does performance collapse?
- Can I safely deploy this implementation across my workload?

ShapeGuard would turn those questions into a reproducible, machine-generated compatibility report.

This is grounded in a broader need AWS itself has identified. Its June 2026 discussion of Neuron Agentic Development describes operator gaps, model-code porting, and correctness validation at scale as important challenges beyond kernel generation alone.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://aws.amazon.com\&sz=32)

Artificial Intelligence



That gives us a better angle than duplicating the existing author-debug-profile workflow: make the agent an automated boundary-discovery and regression-testing system.

I'm not claiming AWS has no internal tools for this. The opportunity is to demonstrate a useful, narrowly scoped capability that complements its existing tooling.

## 1. What makes ShapeGuard different?

Most coding agents follow this loop:

`Write code → test one example → fix error → repeat`

ShapeGuard follows a different loop:

`Generate test → run on hardware → classify result → shrink failures → map boundaries → generate next test`

The key difference is that the next experiment is selected to learn something new about the kernel, rather than simply to produce another implementation.

For example, suppose a kernel works for hidden dimensions 256, 512, and 1024, but fails for 768. A conventional agent might attempt a code fix immediately.

ShapeGuard would investigate:

1. Does the failure occur for every batch size?
2. Does it occur only for non-power-of-two dimensions?
3. Does it fail at compilation, execution, or numerical comparison?
4. What is the smallest input shape that reproduces it?
5. After a fix, does the same failure disappear without introducing regressions?

The result is an engineering artifact that remains useful even after the original agent session ends.

## 2. The killer feature: automatic failure minimization

This is what I would make the centerpiece of the demo.

Suppose ShapeGuard tests a kernel with a tensor of shape `(4, 300, 768)` and gets a numerical mismatch.

That input is not necessarily the root cause. Perhaps the problem occurs only when the last dimension is not divisible by a particular tile size. Or perhaps it is a value-dependent numerical issue.

ShapeGuard would try to find the smallest reproducible counterexample.

## A real engineering investigation, automated

INITIAL FAILURE

Input shape: `(4, 300, 768)`

Numerical checker fails on one configuration.

INVESTIGATION

Test different batch sizes, sequence lengths, dimensions, and values. Keep each test that helps isolate the failure.

MINIMAL REPRODUCER

Hypothesis: A tail tile or reduction boundary is mishandled.

The agent tests this hypothesis rather than assuming it is true.

FINAL ARTIFACT

A small test that reliably reproduces the problem, a failure classification, and a regression test that must pass after a fix.

The precise implementation matters. For numerical failures, ShapeGuard can shrink dimensions and simplify input values while preserving the failure. For compilation failures, it can search nearby shapes and data types to find the boundary between supported and unsupported configurations.

This is a form of counterexample minimization, similar in spirit to techniques used in property-based testing.

The agent must verify that the minimized input still fails. It must never present a guessed root cause as an established fact.

### Why an engineer might care

A 200-line compiler log is expensive to debug. A minimal test that reproduces the problem in seconds is far easier to investigate, share, and turn into a regression test.

Over time, the output could help developers distinguish recurring classes of issues:

- Incorrect handling of irregular tensor dimensions.
- Numerical instability at extreme values.
- Unsupported shape or dtype combinations.
- Compilation or execution failures.
- Performance cliffs associated with specific workload shapes.

ShapeGuard would not claim to identify compiler bugs automatically. It would provide evidence that helps engineers isolate them.

## 3. How the agent would work

I'd use a six-stage pipeline.

Stage 1 — Generate test cases

Start from the supplied kernel and reference implementation. Generate a bounded collection of shapes, data types, and carefully chosen numerical inputs. Prioritize irregular dimensions, tile boundaries, and edge cases.

Stage 2 — Execute on Trainium

Run each supported candidate through the provided hardware execution path. Capture compilation errors, runtime failures, numerical output, and timing information.

Stage 3 — Apply independent checks

Compare outputs against the reference and enforce numerical tolerances and operation-specific invariants. Do not allow the model to override the checker.

Stage 4 — Isolate the failure

Shrink a failing input, vary one dimension at a time, and classify the observed behavior. Keep uncertainty explicit when multiple explanations remain possible.

Stage 5 — Choose the next experiment

Feed the model the evidence and ask it to select a useful next test or propose a targeted correction. Avoid repeating tests that provide no new information.

Stage 6 — Publish the verified operating range

Produce a report of tested configurations, observed failures, minimal reproducers, regression tests, and performance measurements.

The model is the experiment planner and debugging assistant. The checker is the authority. Trainium is the environment in which the evidence is gathered.

That division of responsibility is central to the design.

## 4. What the final output would look like

I'd build a small dashboard or terminal report that produces a compatibility map.

Imagine this illustrative result for one kernel:

## ShapeGuard — Kernel operating envelope

Illustrative output only; these are not measured results.

| Configuration | Verdict     | Finding                         |
| ------------- | ----------- | ------------------------------- |
| Shape A       | Pass        | Correct, stable latency         |
| Shape B       | Fail        | Reproducible numerical mismatch |
| Shape C       | Investigate | Latency regression detected     |
| Shape D       | Unverified  | Not yet tested                  |

### Evidence attached to each verdict

- Exact input shape, dtype, and test seed.
- Reference comparison and numerical error.
- Compiler/runtime output when relevant.
- Measured latency and run-to-run spread.
- Minimal reproducer and regression test, if a failure was found.

I would be careful with the word supported: ShapeGuard should say "passed the tested configurations," not claim that every untested input is safe.

For performance, it should compare repeated measurements under controlled conditions. If a candidate is substantially slower for one shape, it can flag that configuration for investigation rather than assume the slowdown is a hardware defect.

## 5. How to build this in the hackathon without overreaching

The key is to scope it as a demonstrable experiment, not a complete testing platform.

I'd start with one operation from the supplied kernel-agent project and use its existing registration pattern. The event description specifically says a new operation can be added through a NumPy reference, an input builder, and a registration call.

I'd implement these pieces:

| Component         | What I'd build in the hackathon                                 |
| ----------------- | --------------------------------------------------------------- |
| Input generator   | A bounded list of dimensions and edge-case values               |
| Reference checker | Trusted numerical comparison and operation-specific invariants  |
| Hardware runner   | The existing kernel execution harness                           |
| Failure shrinker  | A search over smaller or simpler failing inputs                 |
| Feedback policy   | A few deterministic rules plus model-generated next experiments |
| Attempt logger    | JSONL records of every test and verdict                         |
| Report generator  | A summary of tested shapes, failures, and timings               |

I would not build a complex web application, distributed testing infrastructure, or a general-purpose autonomous coding framework. The terminal output can be the first interface.

### A critical implementation detail

Don't waste time making the model generate a brand-new kernel for every test case.

Start with the supplied candidate and systematically explore its behavior. Only ask the model to modify the kernel when there is a useful failure to investigate. This makes the experiments cheaper, easier to interpret, and more likely to finish in one day.

The supplied model must still be part of the feedback loop, and the checker must still be a genuine artifact that the judges can inspect.

## 6. The experiments that would make this compelling

I would run two primary experiments and one optional experiment.

### Experiment A — Find failures that ordinary tests miss

Compare two test strategies:

- Baseline: A small, conventional set of input shapes.
- ShapeGuard: A bounded, targeted exploration that emphasizes edge cases and boundaries.

Measure:

- Number of hardware executions.
- Number of unique failing configurations found.
- Number of distinct failure classes.
- Time to find the first reproducible failure.
- Number of failures reduced to a minimal reproducer.

The key claim to test is whether targeted exploration finds useful failures more efficiently than the baseline.

### Experiment B — Does shrinking make debugging easier?

For each failure found, measure:

- Original input complexity.
- Minimized input complexity.
- Whether the minimized input still reproduces the same failure.
- Number of hardware runs required.
- Whether the resulting test can be reused as a regression test.

The goal is to turn a hard-to-understand failure into a small, repeatable engineering artifact.

### Optional Experiment C — Discover performance cliffs

For configurations that pass correctness checks, benchmark latency across input shapes.

Report the median, a spread statistic, and the configurations that exhibit unusually high latency relative to neighboring tested shapes.

If the profiler is available, use it to investigate whether those cases exhibit relevant compute or data-movement bottlenecks. AWS's [Neuron performance guide](https://awsdocs-neuron.readthedocs-hosted.com/en/v2.26.0/general/nki/nki_perf_guide.html) describes how input reloads, data spilling, and idle compute engines can affect kernel efficiency.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://awsdocs-neuron.readthedocs-hosted.com\&sz=32)

AWS Neuron Documentation



I would not promise that a shape-dependent slowdown necessarily reveals a compiler problem. It might be an expected consequence of the workload or implementation.

## 7. How I'd divide the work across five people

Person 1 — Hardware execution

Gets the baseline operation running, verifies the provided device environment, and makes the test runner reliable.

Person 2 — Checker

Implements the trusted reference, numerical tolerances, edge cases, and verdict classification.

Person 3 — Test generation and minimization

Builds shape exploration and failure shrinking, with a strict cap on hardware runs.

Person 4 — Agent and analysis

Connects model feedback to the experiment planner, logs every attempt, and evaluates whether the strategy finds failures efficiently.

Person 5 — Research, reporting, and demo

Studies the operation's mathematical properties, designs the baseline comparison, documents the checker, and prepares the final demonstration.

These roles should work in parallel, with the checker contract and test-runner interface agreed upon first.

## 8. The two-minute demo that could win attention

I would show one real bug discovered by the system.

1. Start with a kernel that passes the ordinary test suite. Show the original set of tests and its passing results.
2. Let ShapeGuard explore additional configurations on Trainium. It finds a new failing case that the original suite did not cover.
3. Show the failure shrinker at work. It reduces the failing configuration to a smaller reproducible input.
4. Show the checker evidence. Explain the observed mismatch and the hypothesis being investigated.
5. Fix the issue or demonstrate the regression test. Run the corrected version and show that the minimal reproducer and the previous tests pass.
6. Finish with the compatibility report. Show the exact tested configurations, run count, failure classification, and benchmark statistics.

The ideal result is a bug that is genuinely discovered during the demonstration. If we cannot find one, I'd show the system verifying known-good and deliberately incorrect candidates, while clearly distinguishing injected failures from newly discovered ones.

I would never invent a hardware bug or pretend a scripted failure was discovered autonomously.

## 9. What would make it a true standout rather than just a testing script?

The novelty should live in the experiment planner.

A conventional test suite executes predefined cases. ShapeGuard should decide which case to run next based on the evidence so far.

For example:

- If failures cluster around irregular dimensions, explore nearby dimensions.
- If failures occur only for extreme values, vary the value distribution while holding the shape constant.
- If compilation fails, focus on nearby shape or dtype configurations instead of wasting time on numerical comparisons.
- If the kernel is correct but slow, explore neighboring shapes and use profiling evidence to guide further investigation.
- If the same failure appears repeatedly, stop duplicating it and spend the remaining budget on an unexplored hypothesis.

The simplest implementation is a deterministic experiment policy with model-assisted diagnosis. You do not need a sophisticated reinforcement-learning system.

The resulting system would answer not just "Did this test pass?" but "What should I test next to learn the most about this kernel?"

That is the strongest technical story.

## 10. The exact deliverables I'd submit

Deliverable 1 — The checker

A standalone checker that defines acceptance, explains rejection, and generates reproducible failure reports. Include the reference implementation, numerical tolerances, and tests validating that the checker catches known incorrect results.

Deliverable 2 — The attempt log

A JSONL file containing every experiment, input configuration, verdict, failure reason, next action, and any benchmark measurements. Include unsuccessful and inconclusive runs.

Deliverable 3 — The one-page report

Report the number of hardware runs, tested configurations, failure-discovery results, minimization results, timing spread, and limitations. Compare ShapeGuard with a conventional baseline and make no claims beyond the evidence.

I would also include a short README with a command that reproduces the demonstration.

## My final verdict

If the goal is to make the Annapurna Labs engineers think, "This person understands what it takes to make Trainium useful to real developers," I'd choose ShapeGuard over a generic kernel optimizer.

It has three advantages:

1. It addresses a real engineering concern: discovering correctness and compatibility problems across the many configurations that a model may encounter.
2. It complements existing AWS agentic kernel tools: rather than rebuilding kernel authoring and profiling, it concentrates on systematic boundary discovery and minimal reproducible failures.
3. It can produce a compelling result in a day: one discovered failure, a minimized reproducer, a trusted checker, and a regression test are meaningful even without a dramatic speedup.

The ambition beyond the hackathon would be a reusable testing layer for Trainium kernels and model operators, with compatibility evidence that developers can inspect before deploying a workload.

I would present that as a proposed extension to the Neuron ecosystem—not as a claim that AWS lacks testing tools.

The one-sentence pitch:

> ShapeGuard is an AI-powered hardware testing agent that systematically discovers where Trainium kernels break, reduces failures to minimal reproducible cases, and turns every discovery into a permanent regression test—helping developers trust what they deploy, not just what passes one demo.

That is the project I'd take to an Annapurna engineer and ask them to challenge.