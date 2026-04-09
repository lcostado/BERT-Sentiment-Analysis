# ============================================================
# Script 03: BERT Sentiment Visualization by CES Category
#            Back Bay National Wildlife Refuge
# ============================================================
# Description:
#   Visualizes BERT-classified sentiment (positive / neutral /
#   negative) across CES categories and crowdsourced platforms.
#   Sentiment is assessed only among reviews that mention each
#   CES category (i.e., _bin == 1).
#
# Input:  ces_scored_backbay_bert.csv
#         (output of 01_bert_sentiment.py, enriched with
#          bert_label and bert_score columns)
#
# Output: p_all_faceted  — all platforms in one panel
#         p_alltrails, p_flickr, p_tripadvisor, p_yelp
#         Saved figures: .tiff and .pdf to OUTPUT_DIR
# ============================================================

# ── 0. Libraries ─────────────────────────────────────────────
library(dplyr)
library(tidyr)
library(ggplot2)
library(forcats)
library(scales)
library(stringr)
library(patchwork)

# ── 1. Configuration ─────────────────────────────────────────
# Update INPUT_PATH and OUTPUT_DIR to match your file locations
INPUT_PATH <- "ces_scored_backbay_bert.csv"
OUTPUT_DIR <- "."    # e.g. "C:/Users/lcostado/Desktop"

# ── 2. Label helper (must match Script 02) ───────────────────
label_ces <- function(x) dplyr::recode(x,
  recreation_physical    = "Recreation & physical activity",
  aesthetic_appreciation = "Aesthetic appreciation",
  spiritual_symbolic     = "Spiritual & symbolic",
  educational_scientific = "Educational & scientific",
  social_cohesion        = "Social interaction & cohesion",
  cultural_heritage      = "Cultural heritage"
)

ces_cols <- c(
  "recreation_physical", "aesthetic_appreciation", "spiritual_symbolic",
  "educational_scientific", "social_cohesion", "cultural_heritage"
)

# ── 3. Load data ─────────────────────────────────────────────
bert_df <- read.csv(INPUT_PATH, stringsAsFactors = FALSE)

# ── 4. Pivot to long format, retain only CES-mentioning rows ──
# Sentiment is computed only within reviews that mention a given
# CES category, so proportions reflect how visitors talk about
# that service — not overall platform tone.
sentiment_long <- bert_df %>%
  select(review_id, source, bert_label,
         all_of(paste0(ces_cols, "_bin"))) %>%
  pivot_longer(
    cols      = ends_with("_bin"),
    names_to  = "ces_category",
    values_to = "mentioned"
  ) %>%
  filter(mentioned == 1) %>%
  mutate(
    ces_category = str_remove(ces_category, "_bin"),
    ces_category = label_ces(ces_category),
    bert_label   = factor(
      str_to_title(bert_label),
      levels = c("Positive", "Neutral", "Negative")
    )
  )

# ── 5. Summarise: proportion of each sentiment per CES × source
sentiment_summary <- sentiment_long %>%
  group_by(source, ces_category, bert_label) %>%
  summarise(n = n(), .groups = "drop") %>%
  group_by(source, ces_category) %>%
  mutate(
    n_total = sum(n),
    prop    = n / n_total
  ) %>%
  ungroup()

# ── 6. Color palettes ─────────────────────────────────────────
sentiment_colors <- c(
  "Positive" = "#2A9D8F",
  "Neutral"  = "#A8DADC",
  "Negative" = "#E76F51"
)

# ── 7. Per-platform plot function ────────────────────────────
plot_sentiment_stacked <- function(platform) {

  df_plt <- sentiment_summary %>%
    filter(source == platform) %>%
    mutate(ces_category = fct_reorder(ces_category, n_total))

  # n= label: total reviews per CES category (shown once at bar end)
  n_labels <- df_plt %>%
    filter(bert_label == "Positive") %>%
    mutate(label = paste0("n=", n_total))

  ggplot(df_plt, aes(x = ces_category, y = prop, fill = bert_label)) +
    geom_col(position = "stack", width = 0.7) +
    geom_text(
      data        = n_labels,
      aes(x = ces_category, y = 1.02, label = label),
      hjust       = 0, size = 3, color = "gray30",
      inherit.aes = FALSE
    ) +
    coord_flip() +
    scale_y_continuous(
      labels = percent_format(accuracy = 1),
      expand = expansion(mult = c(0, 0.18))
    ) +
    scale_fill_manual(values = sentiment_colors, name = "Sentiment") +
    labs(
      x     = NULL,
      y     = "% of CES-mentioning reviews",
      title = platform
    ) +
    theme_bw() +
    theme(legend.position = "bottom")
}

# ── 8. Generate individual platform plots ─────────────────────
p_alltrails   <- plot_sentiment_stacked("AllTrails")
p_flickr      <- plot_sentiment_stacked("Flickr")
p_tripadvisor <- plot_sentiment_stacked("TripAdvisor")
p_yelp        <- plot_sentiment_stacked("Yelp")

# ── 9. Faceted figure — all platforms combined ────────────────
p_all_faceted <- ggplot(
    sentiment_summary %>%
      mutate(ces_category = fct_reorder(ces_category, n_total)),
    aes(x = ces_category, y = prop, fill = bert_label)
  ) +
  geom_col(position = "stack", width = 0.7) +
  coord_flip() +
  facet_wrap(~ source, ncol = 2) +
  scale_y_continuous(
    labels = percent_format(accuracy = 1),
    expand = expansion(mult = c(0, 0.12))
  ) +
  scale_fill_manual(values = sentiment_colors, name = "Sentiment") +
  labs(
    x     = NULL,
    y     = "% of CES-mentioning reviews",
    title = "Sentiment by CES category (Back Bay NWR)"
  ) +
  theme_bw() +
  theme(legend.position = "bottom")

# Display
p_all_faceted

# ── 10. Combined patchwork panel ──────────────────────────────
p_combined <- (p_alltrails | p_flickr) / (p_tripadvisor | p_yelp) +
  plot_annotation(
    title   = "Sentiment by CES category — Back Bay NWR",
    caption = "Sentiment classified using cardiffnlp/twitter-roberta-base-sentiment-latest (RoBERTa)"
  )

p_combined

# ── 11. Save figures ──────────────────────────────────────────

# Faceted (single panel) — recommended for publication
ggsave(
  filename    = file.path(OUTPUT_DIR, "Fig_sentiment_ces_faceted.tiff"),
  plot        = p_all_faceted,
  width       = 12, height = 8, units = "in",
  dpi         = 300,
  compression = "lzw"
)
ggsave(
  filename = file.path(OUTPUT_DIR, "Fig_sentiment_ces_faceted.pdf"),
  plot     = p_all_faceted,
  width    = 12, height = 8, units = "in"
)

# Combined patchwork panel
ggsave(
  filename    = file.path(OUTPUT_DIR, "Fig_sentiment_ces_combined.tiff"),
  plot        = p_combined,
  width       = 14, height = 10, units = "in",
  dpi         = 300,
  compression = "lzw"
)
ggsave(
  filename = file.path(OUTPUT_DIR, "Fig_sentiment_ces_combined.pdf"),
  plot     = p_combined,
  width    = 14, height = 10, units = "in"
)

message("Figures saved to: ", OUTPUT_DIR)
