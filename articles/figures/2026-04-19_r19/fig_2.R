#!/usr/bin/env Rscript
# fig_2.R - Channel-Specific Ramps in Pre-Resignation Chief-Sponsorship
#
# NOTE on cohort definition: The paper's hand-coded exit-channel dictionary
# (local-executive runs, court rulings, cabinet appointments) is NOT directly
# present in the public KNA parquets. We therefore proxy the two contrasting
# channels with the closest plausible computation from available fields:
#   - "Likely local-executive exit": SMD members whose last chief-sponsored
#     bill in the assembly term falls in the [-90, +30]-day window around
#     the corresponding local election (Jun 2010 / Jun 2018 / Jun 2022),
#     and who never sponsor again. This proxies the voluntary-exit channel.
#   - "Productivity-matched continuer pool": SMD members whose chief
#     sponsorship continues > 6 months past the local election. We restrict
#     to members whose pre-window monthly rate falls in the same range as
#     the treated cohort to approximate the "level-matched" pool described
#     in the paper's Table 3.
# Court-ruling exits cannot be identified from the parquets alone (would
# require the hand-coded dictionary), so we omit that series and label
# the legend honestly.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- Sys.getenv("KBL_DATA",
  unset = "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-19_r19/fig_2.pdf"

okabe <- c("#E69F00","#56B4E9","#009E73","#0072B2","#D55E00","#CC79A7","#000000")

# Local-election cycles overlapping with assembly terms
specs <- list(
  list(age = 18, election = as.Date("2010-06-02"), term_end = as.Date("2012-05-29")),
  list(age = 20, election = as.Date("2018-06-13"), term_end = as.Date("2020-05-29")),
  list(age = 21, election = as.Date("2022-06-01"), term_end = as.Date("2024-05-29"))
)

process_one <- function(spec) {
  bills_path <- file.path(data_dir, paste0("master_bills_", spec$age, ".parquet"))
  members_path <- file.path(data_dir, paste0("members_", spec$age, ".parquet"))
  if (!file.exists(bills_path) || !file.exists(members_path)) return(NULL)

  bills <- read_parquet(bills_path) %>%
    select(rst_mona_cd, ppsr_kind, ppsl_dt) %>%
    filter(ppsr_kind == "의원", !is.na(rst_mona_cd), !is.na(ppsl_dt)) %>%
    mutate(ppsl_dt = suppressWarnings(as.Date(ppsl_dt))) %>%
    filter(!is.na(ppsl_dt))

  members <- read_parquet(members_path) %>%
    select(mona_cd, election_type)
  smd_ids <- members %>%
    filter(election_type == "지역구") %>%
    pull(mona_cd) %>% unique()
  bills <- bills %>% filter(rst_mona_cd %in% smd_ids)

  ms <- bills %>%
    group_by(rst_mona_cd) %>%
    summarise(
      first_bill = min(ppsl_dt),
      last_bill  = max(ppsl_dt),
      n_total    = n(),
      .groups = "drop"
    )

  trt_lo <- spec$election - 90
  trt_hi <- spec$election + 30
  cont_cut <- spec$election + 180

  ms <- ms %>%
    mutate(
      cohort = case_when(
        n_total >= 5 & last_bill >= trt_lo & last_bill <= trt_hi ~ "treated",
        last_bill >= cont_cut ~ "continuer",
        TRUE ~ NA_character_
      )
    ) %>%
    filter(!is.na(cohort))

  # Compute per-member early-window rate (months -12 to -7 before election)
  early_lo <- spec$election - 365
  early_hi <- spec$election - 180
  early_rates <- bills %>%
    inner_join(ms %>% select(rst_mona_cd, cohort), by = "rst_mona_cd") %>%
    filter(ppsl_dt >= early_lo, ppsl_dt < early_hi) %>%
    group_by(rst_mona_cd) %>%
    summarise(early_n = n(), .groups = "drop") %>%
    mutate(early_rate = early_n / 6)  # 6 months

  ms <- ms %>%
    left_join(early_rates, by = "rst_mona_cd") %>%
    mutate(early_rate = ifelse(is.na(early_rate), 0, early_rate))

  # Level-match continuers to treated range (the paper's "[1.6, 3.6]" box)
  trt_range <- ms %>% filter(cohort == "treated") %>%
    summarise(lo = quantile(early_rate, 0.10, na.rm = TRUE),
              hi = quantile(early_rate, 0.95, na.rm = TRUE))
  if (nrow(trt_range) == 0 || is.na(trt_range$lo) || is.na(trt_range$hi)) {
    return(NULL)
  }

  ms <- ms %>%
    filter(
      cohort == "treated" |
      (cohort == "continuer" & early_rate >= trt_range$lo & early_rate <= trt_range$hi)
    )

  # Build monthly bin counts in months -12 to -1 before election
  bills_with_cohort <- bills %>%
    inner_join(ms %>% select(rst_mona_cd, cohort), by = "rst_mona_cd") %>%
    mutate(days_before = as.numeric(spec$election - ppsl_dt)) %>%
    filter(days_before > 0, days_before <= 365) %>%
    mutate(month_bin = -ceiling(days_before / 30)) %>%
    filter(month_bin >= -12, month_bin <= -1)

  per_member_month <- bills_with_cohort %>%
    group_by(cohort, rst_mona_cd, month_bin) %>%
    summarise(n_chief = n(), .groups = "drop")

  grid <- ms %>% select(rst_mona_cd, cohort) %>%
    tidyr::crossing(month_bin = -12:-1)

  full <- grid %>%
    left_join(per_member_month, by = c("rst_mona_cd", "cohort", "month_bin")) %>%
    mutate(n_chief = ifelse(is.na(n_chief), 0, n_chief))

  full %>%
    group_by(cohort, month_bin) %>%
    summarise(
      mean_chief = mean(n_chief),
      se_chief   = sd(n_chief) / sqrt(n()),
      n_members  = n_distinct(rst_mona_cd),
      .groups = "drop"
    ) %>%
    mutate(age = spec$age)
}

raw <- bind_rows(lapply(specs, process_one))

if (nrow(raw) == 0) {
  # Honest placeholder if data unavailable
  p <- ggplot() +
    annotate("text", x = 0, y = 0, size = 4,
             label = "Figure not directly reproducible from public KNA data.\nSee replication archive.") +
    theme_void() + xlim(-1, 1) + ylim(-1, 1)
  ggsave(out_path, p, width = 7, height = 4.5)
  quit(status = 0)
}

# Pool across assemblies, weighting by number of members in each cohort-month
pooled <- raw %>%
  group_by(cohort, month_bin) %>%
  summarise(
    mean_chief = weighted.mean(mean_chief, w = n_members),
    se_chief   = sqrt(sum((se_chief * n_members)^2) / (sum(n_members)^2)),
    n_members  = sum(n_members),
    .groups = "drop"
  )

cohort_n <- pooled %>%
  group_by(cohort) %>%
  summarise(n = max(n_members), .groups = "drop")

label_for <- function(cohort) {
  n_t <- cohort_n %>% filter(cohort == "treated") %>% pull(n)
  n_c <- cohort_n %>% filter(cohort == "continuer") %>% pull(n)
  if (cohort == "treated") {
    paste0("Likely local-executive exit\n(last bill near local election; n=", n_t, ")")
  } else {
    paste0("Level-matched continuer pool\n(active > 6m post-election; n=", n_c, ")")
  }
}

pooled <- pooled %>%
  mutate(cohort_lab = vapply(cohort, label_for, character(1)))

# Compute simple linear ramp slope (bills per month) for annotation
slopes <- pooled %>%
  group_by(cohort, cohort_lab) %>%
  summarise(
    slope = coef(lm(mean_chief ~ month_bin))[["month_bin"]],
    .groups = "drop"
  )

# Place slope annotations
ann <- slopes %>%
  mutate(
    label = sprintf("ramp = %+0.2f bills/mo", slope),
    x = -11.5,
    y = ifelse(cohort == "treated",
               max(pooled$mean_chief, na.rm = TRUE) * 0.95,
               max(pooled$mean_chief, na.rm = TRUE) * 0.45)
  )

p <- ggplot(pooled, aes(x = month_bin, y = mean_chief,
                        color = cohort_lab, fill = cohort_lab,
                        shape = cohort_lab)) +
  geom_ribbon(aes(ymin = pmax(0, mean_chief - 1.96 * se_chief),
                  ymax = mean_chief + 1.96 * se_chief),
              alpha = 0.15, color = NA) +
  geom_line(linewidth = 0.7) +
  geom_point(size = 2.2) +
  geom_smooth(method = "lm", se = FALSE, linetype = "dashed",
              linewidth = 0.5, formula = y ~ x) +
  geom_text(data = ann,
            aes(x = x, y = y, label = label, color = cohort_lab),
            hjust = 0, size = 3.2, show.legend = FALSE,
            inherit.aes = FALSE) +
  scale_color_manual(values = c(okabe[5], okabe[4])) +
  scale_fill_manual(values = c(okabe[5], okabe[4])) +
  scale_shape_manual(values = c(16, 17)) +
  scale_x_continuous(breaks = seq(-12, -1, by = 2),
                     limits = c(-12.2, -0.5)) +
  labs(
    x = "Months before local election (reference date)",
    y = "Chief-sponsored bills per month (mean)",
    color = NULL, fill = NULL, shape = NULL
  ) +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "bottom",
    legend.text = element_text(size = 8.5),
    legend.key.height = unit(1.4, "lines"),
    panel.grid.minor = element_blank()
  )

ggsave(out_path, p, width = 7, height = 4.5)
