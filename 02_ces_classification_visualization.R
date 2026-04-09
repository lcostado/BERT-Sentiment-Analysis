# ============================================================
# Script 02: CES Keyword Classification and Visualization
#            Back Bay National Wildlife Refuge
# ============================================================
# Description:
#   Classifies crowdsourced platform reviews (AllTrails, Flickr,
#   TripAdvisor, Yelp) into Cultural Ecosystem Services (CES)
#   categories using keyword pattern matching. Produces faceted
#   bar figures showing CES mention proportions by platform.
#
# Input:  ces_analysis  (data frame with columns: review_id, source, reviews)
# Output: yes_ces_scored, ces_summary
#         Figures: p1 (CES mentions faceted), p_all_faceted (saved to disk)
#
# CES categories follow CICES v5.1 / TEEB classification:
#   Recreation & physical activity | Aesthetic appreciation
#   Spiritual & symbolic           | Educational & scientific
#   Social interaction & cohesion  | Cultural heritage
# ============================================================

# ── 0. Libraries ─────────────────────────────────────────────
library(dplyr)
library(stringr)
library(tidyr)
library(ggplot2)
library(forcats)
library(scales)

# ── 1. Helper functions ──────────────────────────────────────

#' Clean raw review text for keyword matching
clean_ces_text <- function(x) {
  x %>%
    coalesce("") %>%
    str_to_lower() %>%
    str_replace_all("http\\S+|www\\S+", " ") %>%
    str_replace_all("\\bgeo:(lat|lon)=\\d+\\b", " ") %>%
    str_replace_all("\\bgeotagged\\b", " ") %>%
    str_replace_all("\\b\\d{8,}\\b", " ") %>%
    str_replace_all("[^[:alnum:][:space:]]+", " ") %>%
    str_squish()
}

#' Count total keyword matches across a list of regex patterns
count_matches <- function(text, patterns) {
  sum(vapply(
    patterns,
    function(p) str_count(text, regex(p, ignore_case = TRUE)),
    integer(1)
  ))
}

#' Recode internal CES variable names to publication labels
label_ces <- function(x) dplyr::recode(x,
  recreation_physical    = "Recreation & physical activity",
  aesthetic_appreciation = "Aesthetic appreciation",
  spiritual_symbolic     = "Spiritual & symbolic",
  educational_scientific = "Educational & scientific",
  social_cohesion        = "Social interaction & cohesion",
  cultural_heritage      = "Cultural heritage"
)

# ── 2. CES keyword patterns (tuned for Back Bay NWR) ─────────
ces_patterns <- list(

  recreation_physical = c(
    "\\bhik(e|ing|ed)?\\b", "\\bwalk(s|ing|ed)?\\b", "\\btrail(s)?\\b",
    "\\bboardwalk(s)?\\b", "\\bwalkway(s)?\\b", "\\bpath(s)?\\b",
    "\\bbik(e|ing|ed)?\\b", "\\bcycl(e|ing|ist|ists)?\\b",
    "\\bkayak(ing)?\\b", "\\bcanoe(ing)?\\b", "\\bpaddl(e|ing|ed)?\\b",
    "\\bfish(ing|ed)?\\b", "\\bcamp(ing|ed)?\\b",
    "\\bbench(es)?\\b", "\\bobservation\\b", "\\bblind(s)?\\b"
  ),

  aesthetic_appreciation = c(
    "\\bbeautiful\\b", "\\bwonderful\\b", "\\bstunning\\b", "\\bgorgeous\\b",
    "\\bscenic\\b", "\\bscenery\\b", "\\bview(s)?\\b", "\\bviews\\b",
    "\\bsunset\\b", "\\bsunrise\\b", "\\bphoto(s|graph(y|ic))?\\b",
    "\\bbeach\\b", "\\bdune(s)?\\b", "\\bocean\\b", "\\blandscape(s)?\\b",
    "\\bpicturesque\\b"
  ),

  spiritual_symbolic = c(
    "\\bspiritual\\b", "\\bsacred\\b", "\\bpray(er|ing)?\\b", "\\bbless(ed|ing)?\\b",
    "\\bpeace(ful)?\\b", "\\bpeace and quiet\\b", "\\bquiet\\b", "\\bcalm\\b",
    "\\bserene\\b", "\\btranquil\\b", "\\brelax\\b", "\\bunwind\\b",
    "\\bescape\\b", "\\bsecluded\\b", "\\bback to nature\\b", "\\bawe\\b"
  ),

  educational_scientific = c(
    "\\bnature center\\b", "\\bvisitor\\s*center\\b", "\\binterpretive\\b",
    "\\bsignage\\b", "\\binformative\\b", "\\beducat(e|ion|ional)?\\b",
    "\\bknowledgeable\\b", "\\bvolunteer\\b", "\\branger\\b", "\\bguided\\s*tour(s)?\\b",
    "\\bwildlife\\b", "\\bbird(s|ing|er|ers)?\\b", "\\bwaterfowl\\b",
    "\\bspecies\\b", "\\bhabitat(s)?\\b", "\\bwetland(s)?\\b", "\\bmarsh\\b",
    "\\becolog(y|ical)\\b", "\\bconserv(e|ation|ing)\\b",
    "\\bbald eagle\\b", "\\bosprey\\b", "\\bpelican(s)?\\b", "\\bplover(s)?\\b",
    "\\bturtle(s)?\\b", "\\bsnake(s)?\\b", "\\bdeer\\b", "\\brabbit\\b"
  ),

  social_cohesion = c(
    "\\bfamily\\b", "\\bkid(s)?\\b", "\\bchildren\\b",
    "\\bfriends\\b", "\\bgroup\\b", "\\btogether\\b",
    "\\bvisiting\\s+family\\b", "\\bwe\\s+visited\\b",
    "\\bpicnic\\b", "\\bgather(ing|ed)?\\b", "\\bshared\\b"
  ),

  cultural_heritage = c(
    "\\bhistory\\b", "\\bhistoric(al)?\\b", "\\bheritage\\b",
    "\\bmuseum\\b", "\\bmonument\\b", "\\bmemorial\\b", "\\blandmark\\b",
    "\\bcultural\\b", "\\btradition(s)?\\b"
  )
)

ces_cols <- names(ces_patterns)

# ── 3. Validate input columns ────────────────────────────────
needed_cols <- c("review_id", "source", "reviews")
missing_cols <- setdiff(needed_cols, names(ces_analysis))
if (length(missing_cols) > 0) {
  stop(paste("ces_analysis is missing columns:", paste(missing_cols, collapse = ", ")))
}

# ── 4. Clean text and score CES (multi-label) ─────────────────
yes_ces_scored <- ces_analysis %>%
  mutate(
    source     = str_squish(source),
    text_clean = clean_ces_text(reviews)
  ) %>%
  rowwise() %>%
  mutate(
    recreation_physical    = count_matches(text_clean, ces_patterns$recreation_physical),
    aesthetic_appreciation = count_matches(text_clean, ces_patterns$aesthetic_appreciation),
    spiritual_symbolic     = count_matches(text_clean, ces_patterns$spiritual_symbolic),
    educational_scientific = count_matches(text_clean, ces_patterns$educational_scientific),
    social_cohesion        = count_matches(text_clean, ces_patterns$social_cohesion),
    cultural_heritage      = count_matches(text_clean, ces_patterns$cultural_heritage)
  ) %>%
  ungroup() %>%
  mutate(
    across(all_of(ces_cols), ~ as.integer(.x > 0), .names = "{.col}_bin"),
    ces_richness = rowSums(across(ends_with("_bin")))
  )

# ── 5. Summary table ─────────────────────────────────────────
ces_long <- yes_ces_scored %>%
  select(review_id, source, ends_with("_bin")) %>%
  pivot_longer(
    cols      = ends_with("_bin"),
    names_to  = "ces_category",
    values_to = "mentioned"
  ) %>%
  mutate(
    ces_category = str_remove(ces_category, "_bin"),
    ces_category = label_ces(ces_category)
  )

ces_summary <- ces_long %>%
  group_by(source, ces_category) %>%
  summarise(
    n             = n(),
    n_mentioned   = sum(mentioned),
    prop_mentioned = n_mentioned / n,
    .groups = "drop"
  )

# ── 6. Color palette ─────────────────────────────────────────
ces_colors <- c(
  "Aesthetic appreciation"         = "#E07428",
  "Social interaction & cohesion"  = "#6AA329",
  "Educational & scientific"       = "#D63384",
  "Spiritual & symbolic"           = "#7B6BB5",
  "Recreation & physical activity" = "#2A9D8F",
  "Cultural heritage"              = "#8B6914"
)

# ── 7. Figure: CES mentions by platform (faceted) ────────────
p1 <- ggplot(ces_summary,
             aes(x    = fct_reorder(ces_category, prop_mentioned),
                 y    = prop_mentioned,
                 fill = ces_category)) +
  geom_col() +
  geom_text(
    aes(label = paste0("n=", n_mentioned)),
    hjust = -0.15, size = 3, color = "gray30"
  ) +
  coord_flip() +
  facet_wrap(~ source, ncol = 2) +
  scale_y_continuous(
    labels = percent_format(accuracy = 1),
    expand = expansion(mult = c(0, 0.18))
  ) +
  scale_fill_manual(values = ces_colors) +
  labs(
    x     = NULL,
    y     = "% of records mentioning CES",
    title = "CES mentions by platform/source (Back Bay NWR)"
  ) +
  theme_bw() +
  theme(legend.position = "none")

p1
