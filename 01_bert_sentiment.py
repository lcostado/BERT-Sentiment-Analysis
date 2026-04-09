"""
01_bert_sentiment.py
--------------------
BERT Sentiment Analysis — Back Bay NWR CES Reviews

Classifies each review as positive, neutral, or negative using a
RoBERTa model fine-tuned on social media text (Cardiff NLP).
Supports Apple Silicon (MPS), CUDA, and CPU automatically.

Input:  ces_scored_backbay.csv   (must contain columns: review_id, source, text_clean)
Output: ces_scored_backbay_bert.csv  (original columns + bert_label, bert_score)

Requirements:
    pip install transformers torch pandas tqdm

Model citation:
    Loureiro et al. (2022). TimeLMs: Diachronic Language Models from Twitter.
    ACL 2022. https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest
"""

import pandas as pd
from transformers import pipeline
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")

# ── Configuration ─────────────────────────────────────────────────────────────
INPUT_PATH  = "ces_scored_backbay.csv"
OUTPUT_PATH = "ces_scored_backbay_bert.csv"
MODEL_NAME  = "cardiffnlp/twitter-roberta-base-sentiment-latest"
BATCH_SIZE  = 32
MAX_TOKENS  = 512    # RoBERTa hard limit; no reviews in this dataset exceed it


# ── Device detection ──────────────────────────────────────────────────────────
def get_device() -> int:
    """Return device index: MPS / CUDA = 0, CPU = -1."""
    import torch
    if torch.backends.mps.is_available():
        print("Device: Apple Silicon GPU (MPS)")
        return 0
    if torch.cuda.is_available():
        print("Device: CUDA GPU")
        return 0
    print("Device: CPU")
    return -1


# ── Model loading ─────────────────────────────────────────────────────────────
def load_model(device: int):
    """Load sentiment pipeline. First run downloads ~500 MB model weights."""
    print(f"Loading model: {MODEL_NAME}")
    print("(First run downloads ~500 MB — subsequent runs use local cache)\n")
    return pipeline(
        "sentiment-analysis",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        truncation=True,
        max_length=MAX_TOKENS,
        device=device,
    )


# ── Inference ─────────────────────────────────────────────────────────────────
def run_sentiment(pipe, texts: list[str]) -> tuple[list[str], list[float]]:
    """
    Run sentiment classification in batches with a progress bar.

    Returns
    -------
    labels : list[str]   'positive' | 'neutral' | 'negative'
    scores : list[float] model confidence for the predicted label (0–1)
    """
    results = []
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Classifying"):
        batch = [t if isinstance(t, str) and t.strip() else "" 
                 for t in texts[i : i + BATCH_SIZE]]
        results.extend(pipe(batch))

    labels = [r["label"].lower() for r in results]
    scores = [round(r["score"], 4) for r in results]
    return labels, scores


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # 1. Load data
    df = pd.read_csv(INPUT_PATH)
    print(f"Loaded {len(df):,} reviews from {df['source'].nunique()} platforms")
    print(f"Platforms: {', '.join(sorted(df['source'].unique()))}\n")

    # 2. Load model
    pipe = load_model(get_device())

    # 3. Run inference
    print(f"Classifying {len(df):,} reviews (batch size = {BATCH_SIZE})...\n")
    labels, scores = run_sentiment(pipe, df["text_clean"].fillna("").tolist())

    # 4. Append results
    df["bert_label"] = labels   # positive | neutral | negative
    df["bert_score"] = scores   # confidence for predicted label

    # 5. Save
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nOutput saved to: {OUTPUT_PATH}")

    # 6. Diagnostic summary
    print("\nOverall sentiment counts:")
    print(df["bert_label"].value_counts().to_string())
    print("\nSentiment counts by platform:")
    print(df.groupby("source")["bert_label"].value_counts().to_string())


if __name__ == "__main__":
    main()
