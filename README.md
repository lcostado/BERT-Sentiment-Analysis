# BERT-Sentiment-Analysis
Sentiment analysis of crowdsourced data using the Bidirectional Encoder Representations from Transformers (BERT)
# CES Crowdsourced Data Analysis — Back Bay NWR

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Reproducible code for the classification and sentiment analysis of crowdsourced platform reviews (AllTrails, Flickr, TripAdvisor, Yelp) for Cultural Ecosystem Services (CES) assessment at Back Bay National Wildlife Refuge (Virginia, USA).

This repository accompanies the manuscript:

> **Laura Costadone and Shan Zhang** (*in review*). *From Reviews to Value: Harnessing Crowdsourced Data to Capture Visitor Perceptions and Economic Benefits of Recreation*. Ecosystems and People.

---

## Repository structure

```
.
├── 01_bert_sentiment.py                 # Python: BERT sentiment classification
├── 02_ces_classification_visualization.R  # R: CES keyword scoring + Figure 1
├── 03_bert_sentiment_visualization.R    # R: Sentiment figures (Figures 2–3)
├── data/
│   ├── ces_scored_backbay.csv           # CES-scored reviews (input to Scripts 02–03)
│   └── ces_scored_backbay_bert.csv      # BERT-enriched output (produced by Script 01)
├── figures/
│   ├── Fig_ces_mentions_faceted.tiff
│   ├── Fig_sentiment_ces_faceted.tiff
│   └── Fig_sentiment_ces_combined.tiff
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

> **Note:** Raw review text is not redistributed in this repository due to platform Terms of Service. The scored datasets (`ces_scored_backbay.csv`, `ces_scored_backbay_bert.csv`) contain processed text and classification results only.

---

## Methods overview

### CES keyword classification (Script 02)

Reviews were classified into six CES categories following CICES v5.1 and TEEB frameworks using regex-based keyword matching:

- Recreation & physical activity
- Aesthetic appreciation
- Spiritual & symbolic
- Educational & scientific
- Social interaction & cohesion
- Cultural heritage

Classification is multi-label: a single review may be assigned to more than one category.

### BERT sentiment analysis (Script 01)

Sentiment was classified using [`cardiffnlp/twitter-roberta-base-sentiment-latest`](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest), a RoBERTa model fine-tuned on social media text (positive / neutral / negative). Sentiment was assessed only among reviews mentioning each CES category.

**Model citation:**
> Loureiro, D., Barbieri, F., Neves, L., Anke, L. E., & Camacho-Collados, J. (2022). TimeLMs: Diachronic Language Models from Twitter. *Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (ACL)*. https://doi.org/10.18653/v1/2022.acl-demo.25

---

## Requirements

### Python (Script 01)

Python 3.9 or higher is required.

```bash
pip install transformers torch pandas
```

> The model download (~500 MB) occurs automatically on first run and is cached locally.

### R (Scripts 02–03)

R 4.2 or higher is required. Install packages with:

```r
install.packages(c("dplyr", "tidyr", "ggplot2", "forcats",
                   "scales", "stringr", "patchwork"))
```

---

## How to reproduce

### Step 1 — Run BERT sentiment classification

```bash
python 01_bert_sentiment.py
```

Edit `INPUT_PATH` and `OUTPUT_PATH` at the top of the script to match your file locations. Output is `ces_scored_backbay_bert.csv`.

### Step 2 — CES classification and Figure 1

Open `02_ces_classification_visualization.R` in RStudio. Ensure `ces_analysis` is loaded in your environment (data frame with columns `review_id`, `source`, `reviews`). Run the full script. This produces:
- `yes_ces_scored` — review-level CES scores
- `ces_summary` — platform × CES summary table
- `p1` — faceted bar figure of CES mentions

### Step 3 — Sentiment figures

Open `03_bert_sentiment_visualization.R` in RStudio. Update `INPUT_PATH` and `OUTPUT_DIR` at the top of the script. Run the full script. This produces:
- `p_all_faceted` — faceted sentiment figure across all platforms
- `p_combined` — patchwork panel with individual platform plots
- Saved `.tiff` and `.pdf` figures in `OUTPUT_DIR`

---

## Contact

**Laura Costadone**  
Assistant Research Professor  
Institute for Coastal Adaptation and Resilience (ICAR)  
Old Dominion University, Norfolk, Virginia  
[lcostado@odu.edu](mailto:lcostado@odu.edu)

---

## License

This code is released under the [MIT License](LICENSE). Please cite the associated manuscript if you use or adapt this code.
