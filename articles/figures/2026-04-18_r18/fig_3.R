# fig_3.R
# Pre-dissolution chief-sponsor trajectory, UPP sub-cohort, December 2014.
#
# The Constitutional Court dissolved the Unified Progressive Party (UPP,
# 통합진보당) on 2014-12-19, during the 19th National Assembly. Five UPP
# members lost their seats. We compare the monthly per-member chief-sponsor
# activity of the UPP sub-cohort against the continuer pool (all other
# 19th-Assembly members who did not exit in this window) across the 12
# months preceding dissolution.
#
# All series are computed from master_bills_19.parquet and members_19.parquet.
# Month 0 = December 2014 (dissolution month).

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

# --- Paths -------------------------------------------------------------------
data_dir <- Sys.getenv("KBL_DATA",
  unset = "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")

bills_path   <- file.path(data_dir, "master_bills_19.parquet")
members_path <- file.path(data_dir, "members_19.parquet")
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-18_r18/fig_3.pdf"

# --- Load --------------------------------------------------------------------
bills <- read_parquet(bills_path) |>
  select(bill_id, rst_mona_cd, ppsr_kind, ppsl_dt) |>
  filter(ppsr_kind == "의원", !is.na(rst_mona_cd), !is.na(ppsl_dt)) |>
  mutate(ppsl_dt = as.Date(ppsl_dt))

members <- read_parquet(members_path) |>
  select(mona_cd, member_name, party)

# --- Cohort definitions ------------------------------------------------------
# Dissolution date
dissolve_date <- as.Date("2014-12-19")

# UPP members in the 19th Assembly (party field captures party-of-record
# for the assembly; UPP = 통합진보당)
upp_mona <- members |>
  filter(grepl("통합진보", party)) |>
  pull(mona_cd) |>
  unique()

# Continuer pool: all other 19th-Assembly members
all_mona <- unique(members$mona_cd)
continuer_mona <- setdiff(all_mona, upp_mona)

n_upp <- length(upp_mona)
n_cont <- length(continuer_mona)

# --- Monthly chief-sponsor counts per member ---------------------------------
# Window: 12 months before dissolution through dissolution month.
# Month offset: 0 = December 2014, -1 = November 2014, etc.
win_start <- as.Date("2013-12-01")
win_end   <- as.Date("2014-12-31")

bills_win <- bills |>
  filter(ppsl_dt >= win_start, ppsl_dt <= win_end) |>
  mutate(
    ym = format(ppsl_dt, "%Y-%m"),
    month_offset = (as.integer(format(ppsl_dt, "%Y")) - 2014) * 12 +
                   (as.integer(format(ppsl_dt, "%m")) - 12)
  )

# Per-member, per-month bill counts, then average by cohort
make_series <- function(mona_set, label) {
  per_member <- expand.grid(
    mona_cd = mona_set,
    month_offset = seq(-12, 0)
  ) |>
    as_tibble() |>
    left_join(
      bills_win |>
        filter(rst_mona_cd %in% mona_set) |>
        count(rst_mona_cd, month_offset, name = "n_bills") |>
        rename(mona_cd = rst_mona_cd),
      by = c("mona_cd", "month_offset")
    ) |>
    mutate(n_bills = replace_na(n_bills, 0))

  per_member |>
    group_by(month_offset) |>
    summarise(
      mean_bills = mean(n_bills),
      se = sd(n_bills) / sqrt(n()),
      .groups = "drop"
    ) |>
    mutate(cohort = label)
}

upp_series <- make_series(upp_mona, sprintf("UPP sub-cohort (N = %d)", n_upp))
cont_series <- make_series(continuer_mona,
  sprintf("Continuer pool (N = %d)", n_cont))

plot_df <- bind_rows(upp_series, cont_series) |>
  mutate(
    lo = pmax(mean_bills - se, 0),
    hi = mean_bills + se
  )

# --- Plot --------------------------------------------------------------------
okabe_ito <- c("#D55E00", "#0072B2")

p <- ggplot(plot_df, aes(x = month_offset, y = mean_bills,
                         color = cohort, fill = cohort, shape = cohort)) +
  geom_ribbon(aes(ymin = lo, ymax = hi), alpha = 0.15, color = NA) +
  geom_line(linewidth = 0.7) +
  geom_point(size = 2) +
  geom_vline(xintercept = 0, linetype = "dashed",
             color = "grey40", linewidth = 0.4) +
  scale_color_manual(values = okabe_ito) +
  scale_fill_manual(values = okabe_ito) +
  scale_shape_manual(values = c(16, 17)) +
  scale_x_continuous(breaks = seq(-12, 0, 2)) +
  labs(
    x = "Months relative to Constitutional Court dissolution (Dec 2014)",
    y = "Mean chief-sponsored bills per member",
    color = NULL, fill = NULL, shape = NULL
  ) +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "bottom",
    legend.margin = margin(0, 0, 0, 0),
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank()
  )

ggsave(out_path, p, width = 7, height = 4.5)
