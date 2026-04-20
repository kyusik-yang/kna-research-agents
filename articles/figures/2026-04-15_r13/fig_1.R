# fig_1.R  -  Coefficient plot: legislator covariates on legal keyword rate,
# before vs. after committee fixed effects, 21st Assembly 국정감사.
#
# The paper's Table 1 uses a hand-coded "career background" subset
# (prosecutors / lawyers / etc.) for 21 legislators.  That hand coding is
# NOT in the public parquet data, so we compute the closest plausible
# quantity: the same reduction-in-coefficient-after-committee-FE pattern
# using the legislator-level covariates that ARE available in the public
# speech metadata (seniority, female, ruling-party).  The legend labels
# the series honestly.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-15_r13/fig_1.pdf"
dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)

speeches_path <- "/Users/kyusik/Desktop/kyusik-github/kr-hearings-data/data/all_speeches_16_22_v9.parquet"

# Legal-keyword regex (Korean).  Covers core legal vocabulary used in the
# paper's keyword-based classifier: law/statute/court/prosecution/trial.
legal_pattern <- paste(
  "법률", "법안", "법령", "법적", "법원", "법무", "사법",
  "위법", "합법", "불법", "적법",
  "헌법", "형법", "민법",
  "소송", "판결", "기소", "수사", "처벌", "검찰", "재판",
  sep = "|"
)

# Pull 21st Assembly 국정감사 speeches by legislators (keeps memory low).
ds <- open_dataset(speeches_path)

speeches <- ds %>%
  filter(term == 21L,
         hearing_type == "\uAD6D\uC815\uAC10\uC0AC",  # 국정감사
         !is.na(member_id),
         !is.na(speech_text),
         nchar(speech_text) >= 10) %>%
  select(member_id, committee_key, speech_text,
         seniority, gender, ruling_status) %>%
  collect()

# Per-speech legal-keyword indicator, then per-legislator aggregation.
speeches <- speeches %>%
  mutate(has_legal = grepl(legal_pattern, speech_text, perl = TRUE))

# Dominant committee = modal committee_key in this venue for each legislator.
dom_comm <- speeches %>%
  count(member_id, committee_key) %>%
  group_by(member_id) %>%
  slice_max(n, n = 1, with_ties = FALSE) %>%
  ungroup() %>%
  select(member_id, dominant_committee = committee_key)

# Seniority can arrive as Korean ordinal (초선/재선/3선/...) or as numeric.
parse_seniority <- function(x) {
  x <- as.character(x)
  out <- suppressWarnings(as.numeric(x))
  kr_map <- c("\uCD08\uC120" = 1, "\uC7AC\uC120" = 2,
              "3\uC120" = 3, "4\uC120" = 4, "5\uC120" = 5,
              "6\uC120" = 6, "7\uC120" = 7, "8\uC120" = 8, "9\uC120" = 9)
  hit <- kr_map[x]
  out[is.na(out)] <- hit[is.na(out)]
  as.numeric(out)
}

leg_panel <- speeches %>%
  group_by(member_id) %>%
  summarize(
    legal_rate   = mean(has_legal, na.rm = TRUE),
    seniority_in = dplyr::first(seniority),
    gender_in    = dplyr::first(gender),
    ruling_in    = dplyr::first(ruling_status),
    n_speeches   = dplyr::n(),
    .groups = "drop"
  ) %>%
  filter(n_speeches >= 5) %>%
  left_join(dom_comm, by = "member_id") %>%
  mutate(
    seniority_num = parse_seniority(seniority_in),
    female  = as.integer(gender_in %in% c("\uC5EC", "F", "female", "Female")),
    ruling  = as.integer(ruling_in %in% c("\uC5EC\uB2F9", "ruling", "Ruling", "\uC9D1\uAD8C\uC5EC\uB2F9"))
  ) %>%
  filter(!is.na(seniority_num), !is.na(female), !is.na(ruling),
         !is.na(dominant_committee))

# Sanity cap: legal_rate is bounded in [0,1] already by construction.
cat(sprintf("N legislators in estimation sample: %d\n", nrow(leg_panel)))

# Model 1: no committee fixed effects.
m1 <- lm(legal_rate ~ seniority_num + female + ruling, data = leg_panel)

# Model 3: with committee fixed effects.
m3 <- lm(legal_rate ~ seniority_num + female + ruling +
           factor(dominant_committee), data = leg_panel)

extract_coefs <- function(mod, model_name) {
  s  <- summary(mod)$coefficients
  keep <- intersect(c("seniority_num", "female", "ruling"), rownames(s))
  tibble(
    term     = keep,
    estimate = s[keep, "Estimate"],
    se       = s[keep, "Std. Error"],
    model    = model_name
  )
}

coef_df <- bind_rows(
  extract_coefs(m1, "Without committee FE"),
  extract_coefs(m3, "With committee FE")
) %>%
  mutate(
    lo = estimate - 1.96 * se,
    hi = estimate + 1.96 * se,
    term_label = dplyr::recode(term,
      "seniority_num" = "Seniority (terms)",
      "female"        = "Female",
      "ruling"        = "Ruling party"
    ),
    model = factor(model,
                   levels = c("Without committee FE", "With committee FE"))
  )

okabe <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
           "#D55E00", "#CC79A7", "#000000")

p <- ggplot(coef_df,
            aes(x = estimate,
                y = factor(term_label,
                           levels = rev(c("Seniority (terms)",
                                          "Female",
                                          "Ruling party"))))) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "grey50") +
  geom_errorbarh(aes(xmin = lo, xmax = hi),
                 height = 0.15, color = okabe[4], linewidth = 0.5) +
  geom_point(size = 2.6, color = okabe[4]) +
  facet_wrap(~ model, nrow = 1, scales = "free_x") +
  labs(
    x = "Coefficient on legal-keyword rate (per-legislator mean, 21st Assembly audit)",
    y = NULL
  ) +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor   = element_blank(),
    panel.grid.major.y = element_blank(),
    strip.background   = element_rect(fill = "grey95", color = NA),
    strip.text         = element_text(face = "bold"),
    plot.margin        = margin(6, 10, 6, 6)
  )

ggsave(out_path, p, width = 7, height = 4.5)

cat(sprintf("Wrote %s\n", out_path))
