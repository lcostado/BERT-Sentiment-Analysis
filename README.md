# CES Crowdsourced Data Analysis — Back Bay NWR

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Reproducible code for Cultural Ecosystem Services (CES) classification and BERT-based sentiment analysis of crowdsourced platform reviews (AllTrails, Flickr, TripAdvisor, Yelp) at Back Bay National Wildlife Refuge, Virginia, USA.

This repository accompanies the manuscript:

> **Laura Costadone and Shan Zhang** (*in review*). *From Reviews to Value: Harnessing Crowdsourced Data to Capture Visitor Perceptions and Economic Benefits of Recreation
*. *Ecosystems and People*.

---

## Repository structure

```
.
├── 00_run_workflow.py                     # Optional: runs the full Python pipeline
├── 01_bert_sentiment.py                   # BERT sentiment classification (Python)
├── 02_ces_classification_visualization.R  # CES keyword scoring + Figure 1 (R)
├── 03_bert_sentiment_visualization.R      # Sentiment figures — Figures 2–3 (R)
├── data/
│   ├── ces_scored_backbay.csv             # CES-scored reviews (input to all scripts)
│   └── ces_scored_backbay_bert.csv        # BERT-enriched output (produced by Script 01)
├── figures/                               # Publication figures (.tiff, .pdf)
├── .gitignore
└── README.md
```

---

## Data

Reviews were collected from four crowdsourced platforms:

| Platform     | n reviews |
|---|---|
| AllTrails    | — |
| Flickr       | — |
| TripAdvisor  | — |
| Yelp         | — |
| **Total**    | **1,165** |

> **Note on data redistribution:** Raw review text is not included in this repository due to platform Terms of Service. The scored CSV files contain cleaned text and classification outputs only.

---

## Methods overview

### Script 02 — CES keyword classification

Reviews are classified into six CES categories following CICES v5.1 and TEEB frameworks using regex-based keyword matching. Classification is multi-label: a single review may be assigned to more than one category.

| Category | Internal code |
|---|---|
| Recreation & physical activity | `recreation_physical` |
| Aesthetic appreciation | `aesthetic_appreciation` |
| Spiritual & symbolic | `spiritual_symbolic` |
| Educational & scientific | `educational_scientific` |
| Social interaction & cohesion | `social_cohesion` |
| Cultural heritage | `cultural_heritage` |

### Script 01 — BERT sentiment analysis

Sentiment is classified using [`cardiffnlp/twitter-roberta-base-sentiment-latest`](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest), a RoBERTa model fine-tuned for three-class sentiment analysis (positive / neutral / negative). Sentiment is assessed only among reviews that mention a given CES category, so proportions reflect how visitors express each service — not overall platform tone.

The script auto-detects available hardware: Apple Silicon GPU (MPS), CUDA GPU, or CPU.

**Model citation:**
> Loureiro, D., Barbieri, F., Neves, L., Anke, L. E., & Camacho-Collados, J. (2022). TimeLMs: Diachronic Language Models from Twitter. *Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (ACL)*. https://doi.org/10.18653/v1/2022.acl-demo.25

---

## Requirements

### Python — Scripts 00 and 01

Python 3.9 or higher. Install dependencies:

```bash
pip install transformers torch pandas tqdm
```

> The BERT model (~500 MB) downloads automatically on first run and is cached locally at `~/.cache/huggingface`. Subsequent runs use the cache.

### R — Scripts 02 and 03

R 4.2 or higher. Install packages:

```r
install.packages(c("dplyr", "tidyr", "ggplot2", "forcats",
                   "scales", "stringr", "patchwork"))
```

---

## How to reproduce

### Option A — Step by step (recommended)

**Step 1: BERT sentiment classification**

```bash
python 01_bert_sentiment.py
```

Edit `INPUT_PATH` and `OUTPUT_PATH` at the top of the script to match your local file locations. This produces `ces_scored_backbay_bert.csv`.

**Step 2: CES classification and Figure 1**

Open `02_ces_classification_visualization.R` in RStudio. Ensure `ces_analysis` is loaded as a data frame with columns `review_id`, `source`, and `reviews`. Run the full script. This produces:
- `yes_ces_scored` — review-level CES binary scores
- `ces_summary` — platform × CES summary table
- `p1` — faceted bar figure of CES mention proportions

**Step 3: Sentiment figures**

Open `03_bert_sentiment_visualization.R` in RStudio. Update `INPUT_PATH` and `OUTPUT_DIR` at the top of the script. Run the full script. This produces:
- `p_all_faceted` — all platforms in a single faceted panel
- `p_combined` — patchwork panel with one plot per platform
- Publication figures saved as `.tiff` (300 dpi, LZW compression) and `.pdf` (vector)

### Option B — Automated pipeline (Python steps only)

```bash
python 00_run_workflow.py
```

This checks packages, runs `01_bert_sentiment.py`, and saves a printed summary to `analysis_summary.txt`. Then proceed to Step 3 above in RStudio.

---

## Output files

| File | Description |
|---|---|
| `ces_scored_backbay_bert.csv` | Original CES scores + `bert_label` + `bert_score` |
| `analysis_summary.txt` | Console summary of sentiment counts by platform |
| `Fig_ces_mentions_faceted.tiff/.pdf` | CES mention proportions by platform (Figure 1) |
| `Fig_sentiment_ces_faceted.tiff/.pdf` | Stacked sentiment bars, faceted (Figure 2) |
| `Fig_sentiment_ces_combined.tiff/.pdf` | Patchwork panel, one plot per platform (Figure 3) |

---

## Contact

**Laura Costadone**  
Assistant Research Professor  
Institute for Coastal Adaptation and Resilience (ICAR)  
Old Dominion University — Norfolk, Virginia  
[lcostado@odu.edu](mailto:lcostado@odu.edu)

---

## License

Code released under the [MIT License](LICENSE). Please cite the associated manuscript if you use or adapt this code in your research.
