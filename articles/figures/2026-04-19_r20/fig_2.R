# fig_2.R
# Cycle-by-cycle decomposition of the local-executive-runner effect.
#
# The paper relies on a hand-coded set of 40 mid-term departures classified
# into five exit channels. That hand-coded classification is NOT in the
# public parquet inventory. The closest plausible computation from the
# available files is a data-driven proxy:
#
#   Proxy "runner" cohort for assembly t and local-election date e:
#     SMD (지역구) members whose LAST chief-sponsored bill falls within the
#     183 days preceding e AND who chief-sponsor no bill between e-183 and
#     e+90 that is later than the last-bill date. Interpreted as members
#     whose observed chief-sponsorship activity ends in the pre-election
#     window, consistent with a mid-term exit to run locally.
#
#   Continuer benchmark: SMD members still chief-sponsoring bills after
#     election date + 90 days (i.e., still active in the post-election month
#     of the assembly).
#
#   Outcome: monthly chief-sponsorship rate in the 6 months [e-183, e],
#     for both cohorts, measured on the same calendar window.
#
# The figure reports (runner - continuer) with a 95% Wald CI per cycle.
# All numbers are computed from master_bills_{18..21}.parquet and
# members_{18..21}.parquet; nothing is hardcoded from the paper body.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- Sys.getenv("KBL_DATA",
  "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-19_r20/fig_2.pdf"
dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)

ok <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
        "#D55E00", "#CC79A7", "#000000")

# Four eligible local-election cycles covered by the Assemblies in the paper.
cycles <- tibble::tibble(
  age           = c(18L, 19L, 20L, 21L),
  cycle_label   = c("18th Assembly\n(2010 local)",
                    "19th Assembly\n(2014 local)",
                    "20th Assembly\n(2018 local)",
                    "21st Assembly\n(2022 local)"),
  election_date = as.Date(c("2010-06-02",
                            "2014-06-04",
                            "2018-06-13",
                            "2022-06-01"))
)

compute_cycle <- function(age_val, election_date) {
  bill_file <- file.path(data_dir, sprintf("master_bills_%d.parquet", age_val))
  mem_file  <- file.path(data_dir, sprintf("members_%d.parquet", age_val))
  if (!file.exists(bill_file) || !file.exists(mem_file)) {
    return(tibble::tibble(age = age_val, effect = NA_real_, se = NA_real_,
                          n_treated = 0L, n_continuer = 0L))
  }

  bills   <- read_parquet(bill_file)
  members <- read_parquet(mem_file)

  smd <- members %>%
    filter(!is.na(election_type), election_type == "지역구") %>%
    distinct(mona_cd)

  chief <- bills %>%
    filter(!is.na(ppsr_kind), ppsr_kind == "의원", !is.na(rst_mona_cd)) %>%
    mutate(ppsl_dt = suppressWarnings(as.Date(as.character(ppsl_dt)))) %>%
    filter(!is.na(ppsl_dt)) %>%
    inner_join(smd, by = c("rst_mona_cd" = "mona_cd")) %>%
    select(rst_mona_cd, ppsl_dt)

  if (nrow(chief) == 0) {
    return(tibble::tibble(age = age_val, effect = NA_real_, se = NA_real_,
                          n_treated = 0L, n_continuer = 0L))
  }

  pre_window  <- election_date - 183
  post_cutoff <- election_date + 90

  last_bill <- chief %>%
    group_by(rst_mona_cd) %>%
    summarise(last_date = max(ppsl_dt, na.rm = TRUE), .groups = "drop")

  treated_ids <- last_bill %>%
    filter(last_date >= pre_window, last_date <= post_cutoff) %>%
    pull(rst_mona_cd)

  continuer_ids <- last_bill %>%
    filter(last_date > post_cutoff) %>%
    pull(rst_mona_cd)

  rate_in_window <- function(ids) {
    if (length(ids) == 0) return(tibble::tibble(rst_mona_cd = character(0), rate = numeric(0)))
    chief %>%
      filter(rst_mona_cd %in% ids,
             ppsl_dt >= pre_window,
             ppsl_dt <= election_date) %>%
      count(rst_mona_cd) %>%
      right_join(tibble::tibble(rst_mona_cd = ids), by = "rst_mona_cd") %>%
      mutate(n = ifelse(is.na(n), 0L, n),
             rate = n / 6)
  }

  tr <- rate_in_window(treated_ids)
  co <- rate_in_window(continuer_ids)

  t_n <- nrow(tr); c_n <- nrow(co)
  if (t_n == 0 || c_n == 0) {
    return(tibble::tibble(age = age_val, effect = NA_real_, se = NA_real_,
                          n_treated = t_n, n_continuer = c_n))
  }

  t_mean <- mean(tr$rate);     c_mean <- mean(co$rate)
  t_var  <- if (t_n > 1) var(tr$rate) else 0
  c_var  <- if (c_n > 1) var(co$rate) else 0
  se <- sqrt(t_var / max(t_n, 1) + c_var / max(c_n, 1))

  tibble::tibble(
    age         = age_val,
    effect      = t_mean - c_mean,
    se          = se,
    n_treated   = as.integer(t_n),
    n_continuer = as.integer(c_n)
  )
}

results <- do.call(rbind, lapply(seq_len(nrow(cycles)), function(i) {
  compute_cycle(cycles$age[i], cycles$election_date[i])
}))

plot_df <- results %>%
  left_join(cycles, by = "age") %>%
  mutate(
    ci_lo = effect - 1.96 * se,
    ci_hi = effect + 1.96 * se,
    xlab  = paste0(cycle_label, "\n(n = ", n_treated, ")")
  ) %>%
  arrange(age) %>%
  mutate(xlab = factor(xlab, levels = xlab))

# Drop rows where the proxy cohort is empty; keep a visible placeholder row
# so the cycle still appears on the axis.
p <- ggplot(plot_df, aes(x = xlab, y = effect)) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "grey40") +
  geom_linerange(aes(ymin = ci_lo, ymax = ci_hi),
                 color = ok[4], linewidth = 0.8, na.rm = TRUE) +
  geom_point(color = ok[4], size = 3, na.rm = TRUE) +
  labs(
    x = NULL,
    y = "Proxy runner effect on monthly chief-sponsorship rate\n(6-month pre-election window, runner - continuer)"
  ) +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    axis.text.x      = element_text(size = 9)
  )

ggsave(out_path, p, width = 7, height = 4.5)
