"""
00_run_workflow.py
------------------
End-to-end runner for the Back Bay NWR CES sentiment analysis pipeline.

Steps
-----
1. Verify required packages are installed
2. Run BERT sentiment classification  (01_bert_sentiment.py)
3. Print a summary report to the console and save to analysis_summary.txt

Visualization is handled separately in R:
    02_ces_classification_visualization.R  — CES keyword figures
    03_bert_sentiment_visualization.R      — BERT sentiment figures

Usage
-----
    python 00_run_workflow.py

Requirements
------------
    pip install transformers torch pandas tqdm
"""

import subprocess
import sys
import os
import importlib.util

# ── Configuration ─────────────────────────────────────────────────────────────
INPUT_CSV   = "ces_scored_backbay.csv"
OUTPUT_CSV  = "ces_scored_backbay_bert.csv"
SUMMARY_TXT = "analysis_summary.txt"

REQUIRED_PACKAGES = {
    "pandas":       "pandas",
    "transformers": "transformers",
    "torch":        "torch",
    "tqdm":         "tqdm",
}


# ── Package check ─────────────────────────────────────────────────────────────
def check_packages():
    """Install any missing packages."""
    missing = [pip for pkg, pip in REQUIRED_PACKAGES.items()
               if not importlib.util.find_spec(pkg)]
    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("Packages installed.\n")
    else:
        print("All required packages are installed.\n")


# ── Summary report ────────────────────────────────────────────────────────────
def write_summary(output_csv: str, summary_path: str):
    """Print and save key statistics from the enriched CSV."""
    import pandas as pd

    df = pd.read_csv(output_csv)
    total = len(df)

    lines = [
        "SENTIMENT ANALYSIS SUMMARY — Back Bay NWR",
        "=" * 60,
        f"Generated : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Input     : {INPUT_CSV}",
        f"Output    : {output_csv}",
        f"Reviews   : {total:,}",
        f"Platforms : {', '.join(sorted(df['source'].unique()))}",
        "",
        "-" * 60,
        "OVERALL SENTIMENT DISTRIBUTION",
        "-" * 60,
    ]

    for label, count in df["bert_label"].value_counts().items():
        lines.append(f"  {label:<12}: {count:5d}  ({count/total*100:.1f}%)")

    lines += [
        "",
        f"  Mean confidence : {df['bert_score'].mean():.3f}",
        "",
        "-" * 60,
        "SENTIMENT BY PLATFORM",
        "-" * 60,
    ]

    for source in sorted(df["source"].unique()):
        sub = df[df["source"] == source]
        lines.append(f"\n  {source}  (n={len(sub):,})")
        for label, count in sub["bert_label"].value_counts().items():
            lines.append(f"    {label:<12}: {count:4d}  ({count/len(sub)*100:.1f}%)")

    lines += [
        "",
        "=" * 60,
        "NEXT STEPS",
        "=" * 60,
        "  1. Open RStudio and run 02_ces_classification_visualization.R",
        "  2. Run 03_bert_sentiment_visualization.R for sentiment figures",
        "  3. Saved figures (.tiff, .pdf) are ready for manuscript submission",
    ]

    report = "\n".join(lines)
    print("\n" + report)

    with open(summary_path, "w") as f:
        f.write(report)
    print(f"\nSummary saved to: {summary_path}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "=" * 60)
    print("  BACK BAY NWR — CES SENTIMENT ANALYSIS PIPELINE")
    print("=" * 60 + "\n")

    if not os.path.exists(INPUT_CSV):
        sys.exit(
            f"ERROR: '{INPUT_CSV}' not found.\n"
            "Place the file in the same directory as this script and re-run."
        )

    print("Step 1/3  Checking packages...")
    check_packages()

    print("Step 2/3  Running BERT sentiment classification...")
    subprocess.run([sys.executable, "01_bert_sentiment.py"], check=True)

    print("\nStep 3/3  Writing summary report...")
    write_summary(OUTPUT_CSV, SUMMARY_TXT)

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\n  Enriched CSV : {OUTPUT_CSV}")
    print(f"  Summary      : {SUMMARY_TXT}")
    print("\n  Open RStudio and run Scripts 02 and 03 to generate figures.\n")


if __name__ == "__main__":
    main()
