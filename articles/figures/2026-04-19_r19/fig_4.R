## fig_4.R
## Distribution of continuer chief-sponsorship rates for the 18th and 20th
## Korean National Assembly cycles, with the treated (local-executive runner)
## cohort's rates marked.
##
## Approximations used, since the paper's hand-coded resignation list is not
## shipped in the public parquets:
##   - "Continuer": members whose last chief-sponsored bill falls within the
##     final six months of the assembly term (i.e., they remained active up to
##     the term boundary).
##   - "Treated cohort (local-executive runner proxy)": members whose last
##     chief-sponsored bill precedes the local-election date in that cycle
##     (June 2, 2010 for the 18th; June 13, 2018 for the 20th) by at least
##     30 days, and who are not continuers.
## Rates are computed as chief-sponsored bills per 30.44-day month over the
## member's pre-period (term start through min(last bill, term_end - 6mo)).

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- Sys.getenv("KBL_DATA",
  unset = "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-19_r19/fig_4.pdf"

okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#000000")

## Assembly term windows and local-election dates
term_windows <- tibble(
  age            = c(18L, 20L),
  term_start     = as.Date(c("2008-05-30", "2016-05-30")),
  term_end       = as.Date(c("2012-05-29", "2020-05-29")),
  local_election = as.Date(c("2010-06-02", "2018-06-13"))
)

## Load member-sponsored bills for the two cycles
bills <- bind_rows(
  read_parquet(file.path(data_dir, "master_bills_18.parquet")),
  read_parquet(file.path(data_dir, "master_bills_20.parquet"))
) %>%
  filter(ppsr_kind == "의원",
         !is.na(rst_mona_cd),
         !is.na(ppsl_dt)) %>%
  mutate(ppsl_dt = as.Date(ppsl_dt)) %>%
  select(age, rst_mona_cd, ppsl_dt)

## Per-member summary, joined with the term windows
member_stats <- bills %>%
  group_by(age, rst_mona_cd) %>%
  summarise(
    n_bills    = n(),
    first_bill = min(ppsl_dt, na.rm = TRUE),
    last_bill  = max(ppsl_dt, na.rm = TRUE),
    .groups    = "drop"
  ) %>%
  inner_join(term_windows, by = "age") %>%
  filter(n_bills >= 1,
         last_bill >= term_start,
         first_bill <= term_end)

## Classify continuers vs. treated (local-executive runner proxy)
member_stats <- member_stats %>%
  mutate(
    continuer        = last_bill >= (term_end - 180),
    exit_before_loc  = last_bill < (local_election - 30) & !continuer,
    pre_period_end   = pmin(last_bill, term_end - 180),
    months_pre       = pmax(
      as.numeric(pre_period_end - term_start) / 30.44, 1
    ),
    rate_pre         = n_bills / months_pre
  )

## Winsorize the upper tail at the 99th percentile for readable x-axis
x_cap <- quantile(member_stats$rate_pre, 0.99, na.rm = TRUE)

continuers <- member_stats %>%
  filter(continuer) %>%
  mutate(rate_plot = pmin(rate_pre, x_cap))

treated <- member_stats %>%
  filter(exit_before_loc) %>%
  mutate(rate_plot = pmin(rate_pre, x_cap))

## Cycle labels, with counts
cycle_labeller <- function(age_vals) {
  counts_c <- table(continuers$age)
  counts_t <- table(treated$age)
  sapply(age_vals, function(a) {
    a <- as.integer(a)
    nc <- ifelse(is.na(counts_c[as.character(a)]), 0, counts_c[as.character(a)])
    nt <- ifelse(is.na(counts_t[as.character(a)]), 0, counts_t[as.character(a)])
    sprintf("Assembly %d  (continuers n=%d, treated proxy n=%d)",
            a, nc, nt)
  })
}

## Plot
treated_key <- bind_rows(
  mutate(treated, series = "Treated proxy (last bill before local election)")
)
continuers_key <- continuers %>%
  mutate(series = "Continuer distribution")

p <- ggplot() +
  geom_histogram(
    data = continuers_key,
    aes(x = rate_plot, fill = series),
    bins = 30, color = "white", alpha = 0.85
  ) +
  geom_vline(
    data = treated_key,
    aes(xintercept = rate_plot, color = series),
    linetype = "dashed", linewidth = 0.5, alpha = 0.9
  ) +
  geom_rug(
    data = treated_key,
    aes(x = rate_plot, color = series),
    sides = "b", length = unit(0.04, "npc"), alpha = 0.9
  ) +
  facet_wrap(~ age, ncol = 1, scales = "free_y",
             labeller = as_labeller(cycle_labeller)) +
  scale_fill_manual(values = c("Continuer distribution" = okabe_ito[2]),
                    name = NULL) +
  scale_color_manual(
    values = c("Treated proxy (last bill before local election)" = okabe_ito[5]),
    name = NULL
  ) +
  labs(
    x = "Pre-period chief-sponsored bills per month",
    y = "Number of continuers"
  ) +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    strip.background = element_rect(fill = "grey95", color = NA),
    strip.text = element_text(face = "plain"),
    legend.position = "bottom",
    legend.box = "vertical",
    legend.margin = margin(t = 0, b = 0),
    legend.key.size = unit(0.9, "lines")
  )

ggsave(out_path, p, width = 7, height = 4.5)
