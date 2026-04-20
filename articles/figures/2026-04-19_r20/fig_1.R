#!/usr/bin/env Rscript
# Figure 1: Continuer pool ramp distribution with treated-cohort location.
#
# Cohort approximation note: the 40-case hand-coded exit-channel dictionary is
# not bundled with the public KNA parquets, so the "clean local-executive
# runner" cohort is approximated as SMD members in the 18th and 20th assemblies
# whose final chief-sponsored bill falls in the four months leading up to the
# mid-term local election and at least six months before assembly end. The
# continuer pool is the complementary SMD set. Ramps are computed as chief-
# sponsored bills per month in the late window (last six months before anchor)
# minus the early window (seven to twelve months before anchor), where the
# anchor is the local-election date for the runner approximation and the
# assembly-end date for continuers.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#000000")

data_dir <- Sys.getenv("KBL_DATA",
  "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")

assembly_end <- list(
  "18" = as.Date("2012-05-29"),
  "20" = as.Date("2020-05-29")
)

local_election <- list(
  "18" = as.Date("2010-06-02"),
  "20" = as.Date("2018-06-13")
)

compute_ramp_table <- function(anchor_date, bills_df, member_ids) {
  early_start <- anchor_date - 365
  early_end   <- anchor_date - 183
  late_start  <- anchor_date - 183
  late_end    <- anchor_date

  w <- bills_df %>%
    filter(rst_mona_cd %in% member_ids,
           ppsl_dt >= early_start, ppsl_dt <= late_end) %>%
    mutate(window = case_when(
      ppsl_dt >= early_start & ppsl_dt <  early_end ~ "early",
      ppsl_dt >= late_start  & ppsl_dt <= late_end  ~ "late",
      TRUE ~ NA_character_
    )) %>%
    filter(!is.na(window)) %>%
    count(rst_mona_cd, window) %>%
    pivot_wider(names_from = window, values_from = n, values_fill = 0)

  if (!"early" %in% names(w)) w$early <- 0
  if (!"late"  %in% names(w)) w$late  <- 0

  # Add members with zero bills in both windows so the distribution is complete
  missing_ids <- setdiff(member_ids, w$rst_mona_cd)
  if (length(missing_ids) > 0) {
    w <- bind_rows(w,
      tibble(rst_mona_cd = missing_ids, early = 0L, late = 0L))
  }

  w %>%
    mutate(early_rate = early / 6,
           late_rate  = late  / 6,
           ramp = late_rate - early_rate)
}

compute_age <- function(age_num) {
  age_str <- as.character(age_num)
  bills <- read_parquet(
    file.path(data_dir, paste0("master_bills_", age_num, ".parquet")))
  members <- read_parquet(
    file.path(data_dir, paste0("members_", age_num, ".parquet")))

  bills_mem <- bills %>%
    filter(ppsr_kind == "\uc758\uc6d0",
           !is.na(rst_mona_cd), !is.na(ppsl_dt)) %>%
    mutate(ppsl_dt = as.Date(ppsl_dt)) %>%
    select(bill_id, rst_mona_cd, ppsl_dt)

  smd_ids <- members %>%
    filter(election_type == "\uc9c0\uc5ed\uad6c") %>%
    distinct(mona_cd) %>%
    pull(mona_cd)

  end_date <- assembly_end[[age_str]]
  le_date  <- local_election[[age_str]]

  last_bill <- bills_mem %>%
    filter(rst_mona_cd %in% smd_ids) %>%
    group_by(rst_mona_cd) %>%
    summarise(last_dt = max(ppsl_dt), .groups = "drop")

  # Runner approximation: last chief-sponsored bill within four months before
  # the local election, and at least six months before assembly end
  runner_ids <- last_bill %>%
    filter(last_dt <= le_date,
           last_dt >= le_date - 120,
           last_dt <  end_date - 180) %>%
    pull(rst_mona_cd)

  continuer_ids <- setdiff(smd_ids, runner_ids)

  cont <- compute_ramp_table(end_date, bills_mem, continuer_ids) %>%
    mutate(group = "Continuer pool (SMD, 18th + 20th)")

  run <- compute_ramp_table(le_date, bills_mem, runner_ids) %>%
    mutate(group = "Local-executive runner approximation")

  bind_rows(cont, run) %>% mutate(age = age_num)
}

all_data <- bind_rows(compute_age(18), compute_age(20))

continuers <- all_data %>%
  filter(group == "Continuer pool (SMD, 18th + 20th)")
runners <- all_data %>%
  filter(group == "Local-executive runner approximation")

cont_mean <- mean(continuers$ramp, na.rm = TRUE)
run_mean  <- mean(runners$ramp, na.rm = TRUE)
n_cont <- nrow(continuers)
n_run  <- nrow(runners)

# Clip extreme outliers only for the x-axis view; keep them in stats
x_lower <- min(c(quantile(continuers$ramp, 0.005, na.rm = TRUE),
                 min(runners$ramp, na.rm = TRUE))) - 0.2
x_upper <- quantile(continuers$ramp, 0.995, na.rm = TRUE) + 0.2

p <- ggplot(continuers, aes(x = ramp)) +
  geom_histogram(aes(y = after_stat(density)),
                 bins = 45,
                 fill = okabe_ito[2], color = "white",
                 alpha = 0.85) +
  geom_vline(xintercept = 0,
             linetype = "dotted", color = "grey35", linewidth = 0.4) +
  geom_vline(xintercept = cont_mean,
             color = okabe_ito[4], linewidth = 0.55,
             linetype = "dashed") +
  geom_vline(xintercept = run_mean,
             color = okabe_ito[5], linewidth = 0.7,
             linetype = "solid") +
  geom_point(data = runners,
             aes(x = ramp, y = 0),
             color = okabe_ito[5], fill = okabe_ito[5],
             shape = 25, size = 2.6, stroke = 0.3) +
  annotate("text",
           x = cont_mean, y = Inf,
           label = sprintf("Continuer mean = %.2f (n = %d)",
                           cont_mean, n_cont),
           hjust = -0.03, vjust = 1.6, size = 3.1,
           color = okabe_ito[4]) +
  annotate("text",
           x = run_mean, y = Inf,
           label = sprintf("Runner-approx. mean = %.2f (n = %d)",
                           run_mean, n_run),
           hjust = 1.03, vjust = 1.6, size = 3.1,
           color = okabe_ito[5]) +
  coord_cartesian(xlim = c(x_lower, x_upper)) +
  labs(x = "Ramp: late rate minus early rate (chief-sponsored bills per month)",
       y = "Density of continuer pool") +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        panel.grid.major.x = element_line(color = "grey92"),
        plot.margin = margin(6, 10, 6, 6))

out_dir <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-19_r20"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
ggsave(file.path(out_dir, "fig_1.pdf"), p,
       width = 7, height = 4.5)
