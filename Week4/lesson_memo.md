# Week 4 Memo: What Building an Eval Protocol Taught Me

I expected the Week 3 result to be the finding: ReAct scored 11/20 against 7/20 for direct answering. It wasn't. Most of what threatened that gap was measurement, not statistics. Ambiguous questions, truncated baseline answers, a tool-parsing failure and a string-based scorer each affected the numbers more than sample size did. The 4-point gap looked like a result, but I couldn't yet say what it was made of.

## Three lessons

**1. The scorer is part of the experiment.** Q06's baseline answer said £94.50 and was marked wrong, because the scorer compares strings and `94.50` does not match `94.5`. A few lines of scoring code were quietly deciding outcomes. I also found that 12 of the baseline's 13 wrong answers stop mid-expression, consistent with the 128-token cap, so many of them may be truncation rather than wrong arithmetic. I'd check the instrument before testing the hypothesis.

**2. Not every failure is a model failure.** In Q13, Q15 and Q17 the model wrote a correct expression with a stray `}` inside the string. The calculator rejected it twice, and the model then answered from memory and got it wrong. Q20 asked for an unknown `x`, which the calculator can't solve. Without a failure taxonomy, all of these would just count as "ReAct got it wrong."

**3. Twenty tasks can't carry a claim.** ReAct won 6 tasks and lost 2, which gives p of about 0.29, and the confidence intervals overlap. Rewording Q07 changed ReAct's answer from 1029 to 1204. The arms also differ in more than the tool: format, token cap and step budget. And the model called the calculator on 19 of 20 tasks, so "uses the tool when needed" had no way to fail, because no task made it unnecessary.

## How this changed the protocol

I made three design decisions. Success, failure and inconclusive thresholds are fixed before any run, so I can't reinterpret results afterwards. A sealed held-out set is scored once, so my own task choices can't flatter the result. A format-matched control arm isolates the calculator from the prompt format.

## What I'm still unsure about

The thresholds (15 points, 1.5× tokens) are judgement calls, and I'd expect to revisit them once the harness exists. The protocol hasn't been run, and the stray-brace fix is a prediction, not a result: when built, it should flip those three tasks. I wrote the protocol after seeing the pilot, which is fine, but only because I've said so.

## A checklist before trusting an eval

- Are the answer keys right, and the questions unambiguous?
- Does the scorer accept every equivalent correct answer?
- Are any outputs cut off by a token limit?
- What else differs between the arms besides the thing I'm testing?
- Did I write the success rule before running?

## If you've just seen 11/20 versus 7/20

Good, you ran it, and it's worth looking at. Before you tell anyone ReAct works, ask what would make you believe it and what would make you drop it. Write that down before the next run. Your result isn't wrong. It just isn't a finding yet.
