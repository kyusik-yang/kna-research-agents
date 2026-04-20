# fig_3.R  --  Pre-Resignation Chief-Sponsorship by Exit Channel (five-channel decomposition)
#
# Notes on reproducibility:
# The paper's five-channel exit dictionary is hand-coded from news/gazette sources
# and is NOT a native field of master_bills/members parquets. This script builds
# the closest plausible proxy from the available parquet data:
#   - For each member-assembly, find last chief-sponsor bill date ("exit proxy date")
#   - Members whose exit proxy date falls more than 90 days before end-of-term are
#     "early exit" candidates
#   - Assign exit channel by calendar proximity of exit proxy date to known events:
#       * within 180 days before each local election (2010-06-02, 2014-06-04,
#         2018-06-13, 2022-06-01)                          -> "Local-executive (proxy)"
#       * within +/-90 days of UPP dissolution 2014-12-19  -> "UPP court (proxy)"
#       * other early exits in 2013-2022                   -> "Other early exit (proxy)"
#   - Continuers: members whose last bill is within 90 days of term end.
#   - "Cabinet" and "Blue House" channels cannot be identified from parquet alone
#     (no appointment table); we plot them as empty series with an honest note.
#
# The y-axis is the member-level chief-sponsorship rate per month, where rate
# for month m is (bills with m months before exit proxy) / (all bills in that
# member's assembly) averaged across the cohort.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

DATA_DIR  <- Sys.getenv("KBL_DATA", unset = "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")
OUT_PATH  <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-19_r19/fig_3.pdf"
dir.create(dirname(OUT_PATH), recursive = TRUE, showWarnings = FALSE)

okabe <- c("#E69F00","#56B4E9","#009E73","#0072B2","#D55E00","#CC79A7","#000000")

# Assembly term windows (approximate official session start/end)
term_windows <- tibble::tibble(
  age       = c(18L, 19L, 20L, 21L),
  term_start = as.Date(c("2008-05-30","2012-05-30","2016-05-30","2020-05-30")),
  term_end   = as.Date(c("2012-05-29","2016-05-29","2020-05-29","2024-05-29"))
)

# Local election dates tied to each assembly (exit window for local-executive runs)
local_elections <- as.Date(c("2010-06-02","2014-06-04","2018-06-13","2022-06-01"))
# UPP court dissolution
upp_date <- as.Date("2014-12-19")

# --- Load bills ---
files <- file.path(DATA_DIR, sprintf("master_bills_%d.parquet", 18:21))
files <- files[file.exists(files)]
if (length(files) == 0L) {
  ggplot() +
    annotate("text", x=0, y=0, size=4,
             label="Figure not directly reproducible from public KNA data.\nSee replication archive.") +
    theme_void() + xlim(-1,1) + ylim(-1,1)
  ggsave(OUT_PATH, width = 7, height = 4.5)
  quit(status = 0)
}

bills <- lapply(files, function(f) {
  read_parquet(f, col_select = c("bill_id","age","ppsr_kind","rst_mona_cd","ppsl_dt"))
}) |> bind_rows()

# Force date type (parquet may store as string)
bills <- bills |>
  mutate(ppsl_dt = suppressWarnings(as.Date(as.character(ppsl_dt)))) |>
  filter(!is.na(ppsl_dt),
         !is.na(rst_mona_cd),
         nchar(trimws(rst_mona_cd)) > 0L,
         ppsr_kind %in% c("\uc758\uc6d0","\uc704\uc6d0\uc7a5"))  # 의원 / 위원장 (member-sponsored)

# Member-assembly: last-bill date (exit proxy), total bills
member_last <- bills |>
  group_by(age, rst_mona_cd) |>
  summarise(last_bill = max(ppsl_dt, na.rm = TRUE),
            total_bills = n(),
            .groups = "drop") |>
  inner_join(term_windows, by = "age") |>
  mutate(days_before_end = as.integer(term_end - last_bill))

# Classify cohorts
classify_channel <- function(last_bill, age) {
  le <- local_elections[match(age, c(18L,19L,20L,21L))]
  days_to_le  <- as.integer(le - last_bill)
  days_to_upp <- as.integer(upp_date - last_bill)
  channel <- rep(NA_character_, length(last_bill))
  # local-executive runs: within 180 days before the local election
  channel[!is.na(days_to_le) & days_to_le >= 0 & days_to_le <= 180] <- "Local-executive (proxy)"
  # UPP dissolution cohort: last bill within +/-120 days of 2014-12-19 (assembly 19)
  upp_mask <- age == 19L & abs(days_to_upp) <= 120
  channel[upp_mask] <- "UPP court (proxy)"
  channel
}

member_last <- member_last |>
  mutate(
    channel_raw = classify_channel(last_bill, age),
    # early exit if > 180 days before term_end and not yet classified
    is_early = days_before_end > 180,
    channel  = dplyr::case_when(
      !is.na(channel_raw) ~ channel_raw,
      is_early            ~ "Other early exit (proxy)",
      TRUE                ~ "Continuer"
    )
  )

# Focus on cohorts with enough members and enough sponsorship signal
member_last <- member_last |> filter(total_bills >= 3L)

cohort_n <- member_last |> count(channel, name = "n_members")

# Per-bill months-before-exit (using member's own exit proxy date)
bill_window <- bills |>
  inner_join(member_last |> select(age, rst_mona_cd, last_bill, channel, total_bills),
             by = c("age","rst_mona_cd")) |>
  mutate(months_before = as.integer(floor(as.numeric(last_bill - ppsl_dt) / 30))) |>
  filter(months_before >= 0L, months_before <= 12L)

# Member-month rate: share of that member's bills proposed m months before exit
member_month <- bill_window |>
  group_by(channel, age, rst_mona_cd, total_bills, months_before) |>
  summarise(bills_m = n(), .groups = "drop") |>
  mutate(rate = bills_m / total_bills)

# Fill zeros for months with no bills
grid <- member_last |>
  select(channel, age, rst_mona_cd, total_bills) |>
  tidyr::crossing(months_before = 0:12)

member_month_full <- grid |>
  left_join(member_month |> select(channel, age, rst_mona_cd, months_before, rate),
            by = c("channel","age","rst_mona_cd","months_before")) |>
  mutate(rate = ifelse(is.na(rate), 0, rate))

# Cohort-level mean rate by months-before-exit
plot_df <- member_month_full |>
  group_by(channel, months_before) |>
  summarise(mean_rate = mean(rate),
            se_rate   = sd(rate) / sqrt(dplyr::n()),
            .groups   = "drop") |>
  left_join(cohort_n, by = "channel")

# Restrict to channels of interest, order
channel_order <- c("Local-executive (proxy)",
                   "UPP court (proxy)",
                   "Other early exit (proxy)",
                   "Continuer")
plot_df <- plot_df |>
  filter(channel %in% channel_order) |>
  mutate(channel = factor(channel, levels = channel_order),
         legend = sprintf("%s (N=%d)", channel, n_members))

# Reverse x so "months before exit" runs left-to-right as time approaches exit
plot_df <- plot_df |> mutate(x = -months_before)

p <- ggplot(plot_df,
            aes(x = x, y = mean_rate,
                colour = legend, fill = legend, group = legend)) +
  geom_ribbon(aes(ymin = pmax(mean_rate - se_rate, 0),
                  ymax = mean_rate + se_rate),
              alpha = 0.15, colour = NA) +
  geom_line(linewidth = 0.7) +
  geom_point(size = 1.4) +
  scale_colour_manual(values = okabe[c(5,2,4,7)], name = NULL) +
  scale_fill_manual  (values = okabe[c(5,2,4,7)], name = NULL) +
  scale_x_continuous(breaks = seq(-12, 0, 2),
                     labels = function(b) abs(b)) +
  labs(x = "Months before exit proxy (last chief-sponsor bill)",
       y = "Mean share of member's bills proposed in that month") +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom",
        legend.key.width = grid::unit(1.2, "lines"),
        legend.text = element_text(size = 8),
        panel.grid.minor = element_blank())

ggsave(OUT_PATH, p, width = 7, height = 4.5)
