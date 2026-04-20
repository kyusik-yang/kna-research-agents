# fig_2.R
# Cycle-level difference-in-differences of local-executive cohort
# against continuer pool, 18th-21st Korean National Assemblies.
#
# Reproducibility note:
# The paper analyses a hand-coded set of 16 members who actually ran
# for provincial governor or mayor. That hand-coded list is not in the
# public KNA parquets. Following the figure brief's "closest plausible
# quantity" rule, the local-executive cohort here is approximated as
# SMD ("지역구") members whose final chief-sponsor bill in the assembly
# falls in the 180 days preceding the relevant nationwide local
# election. The continuer pool is approximated as SMD members whose
# final chief-sponsor bill falls inside the last 30 days of the
# assembly's statutory term (i.e. members who plausibly served out
# the full term). Cycle-level DiD compares the change in chief-sponsor
# bill counts from the early window (days [-360, -180) before each
# member's last bill) to the late window (days [-180, 0]) between the
# two cohorts.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

DATA_DIR <- Sys.getenv(
  "KBL_DATA",
  unset = "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
)
OUT_PATH <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-18_r18/fig_2.pdf"

okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#000000")

# Korean nationwide local-election dates that fall inside each Assembly
# 5th: 2010-06-02 (18th); 6th: 2014-06-04 (19th);
# 7th: 2018-06-13 (20th); 8th: 2022-06-01 (21st)
cycle_calendar <- tibble(
  age           = 18:21,
  start_date    = as.Date(c("2008-05-30", "2012-05-30",
                            "2016-05-30", "2020-05-30")),
  end_date      = as.Date(c("2012-05-29", "2016-05-29",
                            "2020-05-29", "2024-05-29")),
  election_date = as.Date(c("2010-06-02", "2014-06-04",
                            "2018-06-13", "2022-06-01"))
)

EARLY_LO <- 180   # days before last bill (inclusive)
EARLY_HI <- 360   # days before last bill (exclusive)
LATE_LO  <- 0     # days before last bill (inclusive)
LATE_HI  <- 180   # days before last bill (exclusive)

LE_WINDOW_DAYS    <- 180  # months before local election to flag exit
CONT_WINDOW_DAYS  <- 30   # last days of term to flag continuer

cycle_did <- function(asm) {
  cal <- cycle_calendar %>% filter(age == asm)

  bills <- read_parquet(file.path(DATA_DIR, sprintf("master_bills_%d.parquet", asm))) %>%
    filter(ppsr_kind == "의원",
           !is.na(rst_mona_cd),
           !is.na(ppsl_dt)) %>%
    mutate(ppsl_dt = as.Date(ppsl_dt))

  members <- read_parquet(file.path(DATA_DIR, sprintf("members_%d.parquet", asm)))

  smd_ids <- members %>%
    filter(election_type == "지역구") %>%
    pull(mona_cd)

  member_last <- bills %>%
    filter(rst_mona_cd %in% smd_ids) %>%
    group_by(rst_mona_cd) %>%
    summarise(last_bill = max(ppsl_dt),
              n_bills   = dplyr::n(),
              .groups   = "drop") %>%
    filter(n_bills >= 2)  # need enough activity to define windows

  treated_ids <- member_last %>%
    filter(last_bill >= cal$election_date - LE_WINDOW_DAYS,
           last_bill <= cal$election_date) %>%
    pull(rst_mona_cd)

  control_ids <- member_last %>%
    filter(last_bill >= cal$end_date - CONT_WINDOW_DAYS,
           last_bill <= cal$end_date) %>%
    pull(rst_mona_cd)

  # Drop overlap (rare: members whose last bill sits in both windows)
  control_ids <- setdiff(control_ids, treated_ids)

  panel <- bills %>%
    filter(rst_mona_cd %in% c(treated_ids, control_ids)) %>%
    inner_join(member_last %>% select(rst_mona_cd, last_bill),
               by = "rst_mona_cd") %>%
    mutate(days_before = as.numeric(last_bill - ppsl_dt),
           window = case_when(
             days_before >= LATE_LO  & days_before <  LATE_HI  ~ "late",
             days_before >= EARLY_LO & days_before <  EARLY_HI ~ "early",
             TRUE ~ NA_character_
           )) %>%
    filter(!is.na(window))

  member_changes <- panel %>%
    group_by(rst_mona_cd, window) %>%
    summarise(n = dplyr::n(), .groups = "drop") %>%
    pivot_wider(names_from = window, values_from = n, values_fill = 0L) %>%
    mutate(across(any_of(c("early", "late")), as.numeric))

  if (!"early" %in% names(member_changes)) member_changes$early <- 0
  if (!"late"  %in% names(member_changes)) member_changes$late  <- 0

  # Members in the cohort but with zero activity in either window
  # are still informative (early==late==0 -> change==0); include all.
  all_members <- tibble(rst_mona_cd = c(treated_ids, control_ids))
  member_changes <- all_members %>%
    left_join(member_changes, by = "rst_mona_cd") %>%
    mutate(early = ifelse(is.na(early), 0, early),
           late  = ifelse(is.na(late),  0, late),
           change = late - early,
           treated = rst_mona_cd %in% treated_ids)

  agg <- member_changes %>%
    group_by(treated) %>%
    summarise(mean_change = mean(change),
              var_change  = var(change),
              n           = dplyr::n(),
              .groups     = "drop")

  t_row <- agg %>% filter(treated)
  c_row <- agg %>% filter(!treated)

  # Guard against degenerate cycles (no treated or no control)
  if (nrow(t_row) == 0 || nrow(c_row) == 0 ||
      t_row$n < 2 || c_row$n < 2) {
    return(tibble(age = asm,
                  estimate = NA_real_, se = NA_real_,
                  ci_low = NA_real_, ci_high = NA_real_,
                  n_treated = ifelse(nrow(t_row) == 0, 0L, t_row$n),
                  n_control = ifelse(nrow(c_row) == 0, 0L, c_row$n)))
  }

  est <- t_row$mean_change - c_row$mean_change
  se  <- sqrt(t_row$var_change / t_row$n + c_row$var_change / c_row$n)

  tibble(age       = asm,
         estimate  = est,
         se        = se,
         ci_low    = est - 1.96 * se,
         ci_high   = est + 1.96 * se,
         n_treated = t_row$n,
         n_control = c_row$n)
}

did_results <- bind_rows(lapply(18:21, cycle_did))

# Sanity print to console for transparency
print(did_results)

label_caption <- paste0(
  "N (treated, continuer) by cycle: ",
  paste(sprintf("%d: (%d, %d)",
                did_results$age,
                did_results$n_treated,
                did_results$n_control),
        collapse = "; ")
)

p <- ggplot(did_results,
            aes(x = factor(age), y = estimate)) +
  geom_hline(yintercept = 0, linetype = "dashed", colour = "grey40") +
  geom_pointrange(aes(ymin = ci_low, ymax = ci_high),
                  colour = okabe_ito[5],
                  size = 0.55,
                  fatten = 3.2) +
  scale_x_discrete(labels = c("18" = "18th\n(2010 LE)",
                              "19" = "19th\n(2014 LE)",
                              "20" = "20th\n(2018 LE)",
                              "21" = "21st\n(2022 LE)")) +
  labs(x = "Assembly cycle (and contemporaneous local election)",
       y = "DiD estimate: (late - early) bills,\nlocal-executive cohort minus continuer pool",
       caption = label_caption) +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        plot.caption     = element_text(size = 8, colour = "grey30",
                                        hjust = 0))

ggsave(OUT_PATH, p, width = 7, height = 4.5)
