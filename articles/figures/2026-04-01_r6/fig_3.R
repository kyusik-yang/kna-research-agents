#!/usr/bin/env Rscript
# fig_3.R (Version 2, 2026-09-27)
# Seniority composition by gender and mandate type, 20th-22nd Assemblies,
# with seniority measured at each Assembly. Member-terms from the member files.
#
# Version 1 classified members as first-term when the member-file field
# `reelection` read 초선. That field is the member's lifetime term count at data
# collection and has the same value in every Assembly, so it is not seniority at
# an Assembly. This version follows kna_seniority.derive() in the repository
# root: with L the lifetime count, n the number of member files 17-22 the member
# appears in and k the rank of Assembly a among them, the term number at a is
# L - n + k. First-term means a term number of 1.
# All counts and shares are computed from the parquet files.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- Sys.getenv("KNA_DATA_V060")  # published figure: pinned to the kna v0.6.0 data
if (!dir.exists(data_dir)) stop("KNA_DATA_V060 must name the data/processed folder of kna v0.6.0. ",
                             "Run scripts/setup_kna_v060.sh (see KNA_070_PUBLISHED.md).")

out_path <- "articles/figures/2026-04-01_r6/fig_3.pdf"

lifetime_count <- function(x) {
  x <- trimws(as.character(x))
  out <- suppressWarnings(as.integer(sub("\\s*\uc120$", "", x)))
  out[x == "\ucd08\uc120"] <- 1L
  out[x == "\uc7ac\uc120"] <- 2L
  out
}

# --- Member files 17-22 and the term number at each Assembly ---------------
members <- bind_rows(lapply(17:22, function(a) {
  read_parquet(file.path(data_dir, sprintf("members_%d.parquet", a)),
               col_select = c("mona_cd", "sex", "election_type", "reelection")) %>%
    mutate(assembly = a)
})) %>%
  mutate(L = lifetime_count(reelection)) %>%
  arrange(mona_cd, assembly) %>%
  group_by(mona_cd) %>%
  mutate(n_files = n(), k = row_number(), term_number = L - n_files + k) %>%
  ungroup()
stopifnot(!any(is.na(members$term_number)), all(members$term_number >= 1))

members <- members %>%
  filter(assembly %in% 20:22) %>%
  mutate(
    gender   = ifelse(sex == "\uc5ec", "Women", "Men"),
    mandate  = case_when(
      election_type == "\uc9c0\uc5ed\uad6c"         ~ "SMD",
      election_type == "\ube44\ub840\ub300\ud45c" ~ "PR",
      TRUE ~ NA_character_
    ),
    seniority = ifelse(term_number == 1, "First term", "Second term or later")
  ) %>%
  filter(!is.na(mandate))

# --- Counts and shares by Assembly x gender x mandate -----------------------
comp <- members %>%
  count(assembly, gender, mandate, seniority, name = "n") %>%
  complete(assembly, gender, mandate, seniority, fill = list(n = 0)) %>%
  group_by(assembly, gender, mandate) %>%
  mutate(total = sum(n), share = n / total) %>%
  ungroup() %>%
  mutate(
    group_label = factor(paste(gender, mandate),
                         levels = c("Women PR", "Women SMD", "Men PR", "Men SMD")),
    seniority = factor(seniority, levels = c("First term", "Second term or later")),
    assembly_lab = factor(c("20" = "20th Assembly", "21" = "21st Assembly", "22" = "22nd Assembly")[as.character(assembly)],
                          levels = c("20th Assembly", "21st Assembly", "22nd Assembly"))
  )
print(comp %>% select(assembly, group_label, seniority, n, total) %>% arrange(assembly, group_label, seniority),
      n = 50)

totals <- comp %>% distinct(assembly_lab, group_label, total)

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
    breaks = seq(0, 1, 0.25),
    labels = scales::percent_format(accuracy = 1),
    expand = expansion(mult = c(0, 0.12)),
    limits = c(0, 1.1)
  ) +
  scale_fill_manual(values = c("First term" = okabe[2],
                               "Second term or later" = okabe[5]),
                    name = "Term at that Assembly") +
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

dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
pdf(out_path, width = 7, height = 4.5, useDingbats = FALSE)
print(p)
invisible(dev.off())
cat("Wrote:", out_path, "\n")
