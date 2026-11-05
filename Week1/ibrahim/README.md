# Gemma 4 Tokenizer Probing

A notebook experiment to see **how pre-trained model (Gemma 4) tokenizes text**, and what the model receives for each token. It is the Gemma equivalent of a `tiktoken` per-token probe.

## Model used

| Item | Value |
|---|---|
| Model | `google/gemma-4-E4B-it` |
| Loader | `AutoModelForMultimodalLM` (Hugging Face `transformers`) |
| Processor | `AutoProcessor` (the text tokenizer is at `processor.tokenizer`) |
| Tokenizer class | `GemmaTokenizer` (fast, SentencePiece-style) |
| Device | `device_map="auto"` |


## Steps in probing

### 1. Load the processor and extract the tokenizer
Use `processor.tokenizer` for text-only probing. Calling the full processor can drop tokenizer-specific arguments.

### 2. Encode a string to token IDs
```python
ids = tok("Flow Research", add_special_tokens=False)["input_ids"]
```
Set `add_special_tokens=True` to check whether a BOS token is prepended.

### 3. Convert IDs to raw vocabulary pieces
```python
pieces = tok.convert_ids_to_tokens(ids)
```
It shows the real vocab entries:
- `▁` marks a leading space.
- `<0xNN>` is a byte-fallback token for characters not in the vocab.

### 4. Decode each token individually
```python
decoded = [tok.decode([i]) for i in ids]
```
