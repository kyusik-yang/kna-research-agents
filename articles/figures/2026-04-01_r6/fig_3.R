#!/usr/bin/env Rscript
# fig_3.R
# Seniority composition by gender and mandate type, 20th-22nd Assemblies.
# Data: members_{20,21,22}.parquet from KNA processed data.
# All counts/shares are computed from parquet; nothing is hardcoded.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- Sys.getenv("KBL_DATA",
                       "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")

out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-01_r6/fig_3.pdf"

# --- Load members for the three assemblies --------------------------------
load_members <- function(age) {
  p <- file.path(data_dir, sprintf("members_%d.parquet", age))
  arrow::read_parquet(p) %>%
    mutate(assembly = age)
}

members <- bind_rows(lapply(20:22, load_members))

# --- Clean and classify ---------------------------------------------------
# sex: 남 = Male, 여 = Female
# election_type: 지역구 = SMD, 비례대표 = PR
# reelection: 초선 = first-term; anything else (재선/3선/4선/...) = multi-term
members <- members %>%
  filter(!is.na(sex), !is.na(election_type), !is.na(reelection)) %>%
  mutate(
    gender   = ifelse(sex == "여", "Women", "Men"),
    mandate  = case_when(
      election_type == "지역구"   ~ "SMD",
      election_type == "비례대표" ~ "PR",
      TRUE ~ NA_character_
    ),
    seniority = ifelse(reelection == "초선", "First-term", "Multi-term")
  ) %>%
  filter(!is.na(mandate))

# --- Aggregate: counts and shares by assembly x gender x mandate ----------
comp <- members %>%
  group_by(assembly, gender, mandate, seniority) %>%
  summarise(n = n(), .groups = "drop") %>%
  group_by(assembly, gender, mandate) %>%
  mutate(
    total = sum(n),
    share = n / total
  ) %>%
  ungroup() %>%
  mutate(
    group_label = paste(gender, mandate),
    group_label = factor(group_label,
                         levels = c("Women PR", "Women SMD",
                                    "Men PR",   "Men SMD")),
    seniority   = factor(seniority, levels = c("First-term", "Multi-term")),
    assembly_lab = factor(sprintf("%dth Assembly", assembly),
                          levels = c("20th Assembly",
                                     "21st Assembly",
                                     "22nd Assembly"))
  )

# Fix ordinal labels (20 -> "20th", 21 -> "21st", 22 -> "22nd")
comp$assembly_lab <- factor(
  dplyr::recode(as.character(comp$assembly),
                "20" = "20th Assembly",
                "21" = "21st Assembly",
                "22" = "22nd Assembly"),
  levels = c("20th Assembly", "21st Assembly", "22nd Assembly")
)

# Totals per bar (for annotation above the bar)
totals <- comp %>%
  distinct(assembly_lab, group_label, total)

# --- Plot -----------------------------------------------------------------
okabe <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
           "#D55E00", "#CC79A7", "#000000")

p <- ggplot(comp, aes(x = group_label, y = share, fill = seniority)) +
  geom_col(width = 0.75, colour = "white", linewidth = 0.25) +
  geom_text(
    data = comp %>% filter(share >= 0.08),
    aes(label = sprintf("%.0f%%", 100 * share)),
    position = position_stack(vjust = 0.5),
    size = 3, colour = "white"
  ) +
  geom_text(
    data = totals,
    aes(x = group_label, y = 1.04, label = sprintf("n=%d", total)),
    inherit.aes = FALSE,
    size = 2.8, colour = "grey25"
  ) +
  facet_wrap(~ assembly_lab, nrow = 1) +
  scale_y_continuous(
    labels = scales::percent_format(accuracy = 1),
    expand = expansion(mult = c(0, 0.12)),
    limits = c(0, 1.1)
  ) +
  scale_fill_manual(values = c("First-term" = okabe[2],
                               "Multi-term" = okabe[5]),
                    name = "Seniority") +
  labs(x = NULL, y = "Share within cohort") +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    strip.background   = element_rect(fill = "grey92", colour = NA),
    strip.text         = element_text(face = "bold"),
    axis.text.x        = element_text(angle = 25, hjust = 1),
    legend.position    = "bottom",
    legend.title       = element_text(face = "bold")
  )

# --- Save -----------------------------------------------------------------
dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
ggsave(out_path, p, width = 7, height = 4.5)
