# Systematically Varying Few-Shot Examples

## Overview
This repository/report investigates how few-shot examples (demonstrations) influence the output quality of language models on a fixed task (sentiment analysis). We systematically vary the **count**, **format**, and **sampling parameters** and document what actually moves output quality, using `gpt2` and `Qwen/Qwen2.5-0.5B` as our test models.

## Hypotheses & Results Summary

| Experiment / Variable | Hypothesis (What we tested) | Result (What actually happened) |
| :--- | :--- | :--- |
| **1. Number of Demonstrations ($k$)** | Performance improves and stabilizes as the number of examples ($k$) increases. | **GPT-2:** Accuracy peaks early ($k=2$), higher $k$ shifts prediction bias heavily to negative rather than improving accuracy.<br>**Qwen:** Zero-shot is already near-perfect; increasing $k$ primarily improves format adherence (`label_mass` from ~26% to ~100%). |
| **2. Format of Examples** | Formats that look like natural text or Q&A improve the model's ability to continue the pattern. | **GPT-2:** Accuracy differences are within noise, but format causes massive shifts in bias. The `qa` format gives the best format adherence.<br>**Qwen:** Remains at ceiling across all. The `qa` format yields perfect accuracy and adherence. |
| **3. Context Window Budget** | Demonstrations quickly consume the token budget, especially verbose formats. | **GPT-2 (1024 tokens):** Fits ~47 labelled demos. The `qa` format is ~40% more expensive.<br>**Qwen (32768 tokens):** Fits ~1685 demos.<br>*Takeaway:* Always check prompt length; default right-side truncation deletes the actual query. |
| **4. Sampling Parameters** | Temperature, top-k, and top-p control output diversity predictably across prompts. | **Factual Prompts (Low Entropy):** Model is highly confident; filters have minimal impact on diversity.<br>**Ambiguous Prompts (High Entropy):** Filters and temperature drastically alter diversity and text randomness. |

## Outputs
The execution produces a `week2_results.csv` file containing the logged metrics (accuracy, prediction bias, label mass, and sampling entropy) across all evaluated sweeps.
