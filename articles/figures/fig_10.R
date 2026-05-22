#!/usr/bin/env Rscript

# fig_10.R
# Histogram of beopsawi (Legislation and Judiciary Committee) dwell times
# in the 22nd Assembly. The dashed vertical line marks the 60-day threshold
# at which direct-referral eligibility is triggered.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
})

# Okabe-Ito colorblind-safe palette
okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#F0E442", "#000000")

# Paths
data_dir <- "/Users/kyusik/kna/data/processed/"
out_path <- "/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_10.pdf"

# Load 22nd Assembly bills and member info
bills_22 <- read_parquet(file.path(data_dir, "master_bills_22.parquet"))
members  <- read_parquet(file.path(data_dir, "member_info_17_22.parquet"))

# Filter to member-sponsored bills, then join sponsor info
bills_joined <- bills_22 |>
  filter(ppsr_kind == "의원") |>
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "age" = "assembly"))

# Identify beopsawi (Legislation and Judiciary Committee) referral and
# processing date columns. Different snapshots use slightly different names,
# so we try the most common pairs in order of preference.
date_cols <- names(bills_joined)
candidate_pairs <- list(
  c("law_submit_dt",      "law_proc_dt"),
  c("law_present_dt",     "law_proc_dt"),
  c("law_present_dt",     "law_proc_result_dt"),
  c("beopsawi_submit_dt", "beopsawi_proc_dt"),
  c("rgs_proposed_dt",    "law_proc_dt")
)

dwell_days <- NULL
used_pair  <- NULL
for (pair in candidate_pairs) {
  if (all(pair %in% date_cols)) {
    start_dt   <- as.Date(bills_joined[[pair[1]]])
    end_dt     <- as.Date(bills_joined[[pair[2]]])
    dwell_days <- as.numeric(difftime(end_dt, start_dt, units = "days"))
    used_pair  <- pair
    break
  }
}

# Fallback: any pair of date columns whose names mention "law"
if (is.null(dwell_days)) {
  law_cols <- grep("law", date_cols, value = TRUE, ignore.case = TRUE)
  if (length(law_cols) >= 2) {
    start_dt   <- as.Date(bills_joined[[law_cols[1]]])
    end_dt     <- as.Date(bills_joined[[law_cols[2]]])
    dwell_days <- as.numeric(difftime(end_dt, start_dt, units = "days"))
    used_pair  <- law_cols[1:2]
  }
}

if (is.null(dwell_days)) {
  stop("Could not identify beopsawi dwell-time columns in master_bills_22.parquet")
}

message("Using date columns: ", paste(used_pair, collapse = " -> "))

# Keep non-negative dwell times; cap at 200 days for readability
plot_df <- tibble(dwell_days = dwell_days) |>
  filter(!is.na(dwell_days), dwell_days >= 0, dwell_days <= 200)

# 5-day bins so the 60-day threshold falls cleanly on a bin edge
p <- ggplot(plot_df, aes(x = dwell_days)) +
  geom_histogram(binwidth = 5, boundary = 0,
                 fill = okabe_ito[4], color = "white", linewidth = 0.3) +
  geom_vline(xintercept = 60, linetype = "dashed",
             color = okabe_ito[5], linewidth = 0.6) +
  annotate("text", x = 60, y = Inf,
           label = "60-day threshold",
           hjust = -0.05, vjust = 1.6,
           color = okabe_ito[5], size = 3.2) +
  scale_x_continuous(breaks = seq(0, 200, 20)) +
  labs(x = "Days in beopsawi (Legislation and Judiciary Committee)",
       y = "Number of bills") +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank())

ggsave(out_path, plot = p, width = 7, height = 4.5)
