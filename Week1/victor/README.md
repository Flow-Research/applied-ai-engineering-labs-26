# Week 1: Tokenizer edge-case probe

This submission probes the `o200k_base` tokenizer used by GPT-4o and records how formatting, typos, invented words, and language choice affect tokenization.

## Notebook

- [`week1_tokenizer_probe.ipynb`](week1_tokenizer_probe.ipynb)
- [Kaggle run](https://www.kaggle.com/code/chuloway/tokenizer-probe)

## Observations

| Probe | Observed result |
|---|---|
| Baseline | `Hello world` is encoded as 2 tokens. |
| Trailing space | Adding a trailing space increases the input to 3 tokens. |
| Typo-heavy text | `i wan't you t elp me run tis code` expands to 11 tokens. |
| Invented word | `codehashira` is split into smaller subword pieces. |

The experiment shows that small input changes can increase token count and therefore context and API cost. It also motivates input normalization where preserving the user's exact spelling is not required.

## Limitations

- The notebook probes one tokenizer and does not compare two pretrained models.
- It examines tokenization only; it does not measure next-token distributions or model logits.
- The examples are demonstrations rather than a statistically representative benchmark.
