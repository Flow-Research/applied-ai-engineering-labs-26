# Week 4 Brief: Designing a Rigorous Eval Protocol

Applied AI Research Engineering Fellowship, Phase 1 (Research methodology)

**Goal.** Design, on paper, an evaluation protocol for one claim about the Week 3 ReAct system, with success and failure criteria written before any run. Anchor reading: *AI Agents That Matter* (Kapoor et al., 2025). The question for the week: what would I need to see to believe this claim, and what would change my mind?

## Your claim

| Claim | The question it asks | Your protocol must pin down |
| --- | --- | --- |
| ReAct beats direct answering | Is the gain real and caused by the tool? | A fair baseline, a control arm, a minimum effect size |
| The model calls the tool when it needs it | Is tool use appropriate, or just habitual? | What counts as "needed", and how you label it |
| ReAct's gain is worth its extra cost | Does accuracy justify tokens, steps and time? | Your cost definition and a threshold |
| The scorer measures correctness validly | Can the scorer mark right answers wrong, or wrong ones right? | A check set with known answers and an error rate |
| The result holds on harder or different tasks | Does it generalise beyond your task set? | Task strata, a held-out set, what would break it |

## Ground rules

- Everyone uses the shared Week 3 code on GitHub. Use it as is for the audit and the protocol.
- Use your own saved results and traces (`week3_results.json`) as pilot data. If you have none, build a small task set and run it first.
- Arms, sample size and decision rules are your own design choices.
- The protocol is a design on paper. You are not expected to build the full harness this week.
- Optional: make **one** small change to the code, documented (see Workflow, step 3).

## Workflow (about 20 hours)

1. **Pilot data (3h).** Open your results, count your tasks, compute accuracy for both arms, the tool-use rate and a confidence interval, then read the traces. Audit the setup before you trust it. Fold the Kapoor reading into this step and the next.
2. **Write the protocol (8h).** The core deliverable. It must contain: a falsifiable hypothesis and minimum effect size; arms, including a control; task set and holdout; sample-size reasoning; metrics, including cost; success, failure and inconclusive criteria; threats to validity.
3. **Optional rerun (3h).** Fix one flaw from your audit, rerun on the same tasks, and report how far the result moved. Keep the original results alongside.
4. **Peer review (3h).** Critique a peer's protocol: find a confound, a way the result could appear without the claim being true, or an underpowered comparison. Comment on their PR.
5. **Talk prep (3h).**

## Submitting your work

Work on your own branch and add files only inside your own folder. Never edit the original Week 3 code or anyone else's files.

```
git clone <repo-url> && cd <repo-name>        # first time only
git checkout research && git pull origin research
git checkout -b week4_<firstname>
# add your files, then:
git add week4/<firstname>/
git commit -m "Add week 4 protocol and memo"
git push origin week4_<firstname>
```

Open a pull request on GitHub with base `research` and compare `week4_<firstname>`. The team lead merges it. To revise, push to the same branch.

```
week4/<firstname>/
├── protocol.md
├── lesson_memo.md
├── results_original.json
├── results_modified.json       (only if you did the rerun)
├── CHANGES.md                  (only if you did the rerun)
└── week3_react_modified.py     (only if you changed the code)
```

For a code change, edit the copy in your folder, make one change per commit with a clear message, and never overwrite `results_original.json`.

## Deliverables and Friday session

- **Protocol** (2 to 3 pages): how you would test your claim, detailed enough for someone else to run it.
- **Memo** (1 to 2 pages, `lesson_memo.md`): what you learned about evaluating claims rigorously, using your protocol as the worked example.
- **PR submitted 24 hours before the Friday session.**
- **Talk (5 minutes, 70-minute session):** the claim and what your pilot showed (1 min); the biggest flaw you found (1.5 min); your protocol, arms, sample size and decision rule (1.5 min); one finding from review or the rerun, and what would change your mind (1 min).

## How it is judged

Falsifiable hypothesis with a stated effect size; confounds identified and a control that isolates one; sample size justified with honest uncertainty; success, failure and inconclusive criteria fixed in advance; cost treated as a first-class metric; limitations stated honestly, not defended.
