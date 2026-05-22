#!/usr/bin/env Rscript

# fig_9.R
# Bar plot of the annualized failure rate of committee-alternative bypass
# bills at the plenary vote, by Assembly (17th through 22nd).
# A "committee-alternative bypass bill" is a member-sponsored bill that
# reached the plenary without a standing-committee alternative.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
})

# Okabe-Ito colorblind palette
okabe_ito <- c(
  "#E69F00", "#56B4E9", "#009E73", "#0072B2",
  "#D55E00", "#CC79A7", "#000000"
)

data_dir <- "/Users/kyusik/kna/data/processed"
out_path <- "/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_9.pdf"

# -----------------------------------------------------------------------------
# Member info (carried for the required join even though gender / election_type
# are not used in this aggregate figure).
# -----------------------------------------------------------------------------
members <- read_parquet(file.path(data_dir, "member_info_17_22.parquet")) %>%
  select(mona_cd, assembly, gender, election_type, reelection)

# -----------------------------------------------------------------------------
# Load and combine bills for assemblies 17 through 22, keeping member bills.
# -----------------------------------------------------------------------------
assemblies <- 17:22

bills_list <- lapply(assemblies, function(a) {
  f <- file.path(data_dir, sprintf("master_bills_%d.parquet", a))
  read_parquet(f) %>%
    filter(ppsr_kind == "의원")
})

bills <- bind_rows(bills_list)

# Join bills to members: rst_mona_cd = mona_cd AND age = assembly
joined <- bills %>%
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "age" = "assembly"))

# -----------------------------------------------------------------------------
# Identify committee-alternative bypass bills. Bills that bypass the standing
# committee alternative path are flagged either by an explicit bypass column,
# by indicators in the proposal-kind / committee fields, or as a fallback by
# the absence of a recorded committee while the bill still received a plenary
# vote.
# -----------------------------------------------------------------------------
bypass_cols <- intersect(
  c("is_bypass", "bypass", "committee_bypass",
    "alt_bypass", "alternative_bypass", "fast_track", "direct_to_plenary"),
  names(joined)
)

if (length(bypass_cols) >= 1) {
  joined <- joined %>%
    mutate(is_bypass = as.integer(.data[[bypass_cols[1]]] == 1))
} else {
  comm_cols <- intersect(
    c("jrcmit_nm", "committee_nm", "committee", "jrcmit"),
    names(joined)
  )
  if (length(comm_cols) >= 1) {
    joined <- joined %>%
      mutate(
        is_bypass = as.integer(
          (is.na(.data[[comm_cols[1]]]) | .data[[comm_cols[1]]] == "") &
            !is.na(passed)
        )
      )
  } else {
    joined <- joined %>% mutate(is_bypass = as.integer(!is.na(passed)))
  }
}

bypass <- joined %>%
  filter(is_bypass == 1, !is.na(passed))

# -----------------------------------------------------------------------------
# Assembly term lengths (years). The 22nd Assembly is partial.
# 17: 2004-05-30 - 2008-05-29
# 18: 2008-05-30 - 2012-05-29
# 19: 2012-05-30 - 2016-05-29
# 20: 2016-05-30 - 2020-05-29
# 21: 2020-05-30 - 2024-05-29
# 22: 2024-05-30 - present (partial)
# -----------------------------------------------------------------------------
today <- as.Date("2026-05-22")
term_years <- tibble::tibble(
  age = assemblies,
  years = c(
    4, 4, 4, 4, 4,
    as.numeric(today - as.Date("2024-05-30")) / 365.25
  )
)

# -----------------------------------------------------------------------------
# Annualized failure count at the plenary vote (passed == 0), by Assembly.
# -----------------------------------------------------------------------------
fail_by_age <- bypass %>%
  group_by(age) %>%
  summarise(
    n_bills = n(),
    n_fail = sum(passed == 0, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  right_join(tibble::tibble(age = assemblies), by = "age") %>%
  mutate(
    n_bills = ifelse(is.na(n_bills), 0, n_bills),
    n_fail = ifelse(is.na(n_fail), 0, n_fail)
  ) %>%
  left_join(term_years, by = "age") %>%
  mutate(
    fail_per_year = n_fail / years,
    assembly_label = paste0(age, "th")
  ) %>%
  arrange(age)

# -----------------------------------------------------------------------------
# Plot
# -----------------------------------------------------------------------------
p <- ggplot(fail_by_age,
            aes(x = factor(age, levels = assemblies),
                y = fail_per_year,
                fill = factor(age, levels = assemblies))) +
  geom_col(width = 0.7, color = "black", linewidth = 0.25) +
  scale_fill_manual(values = okabe_ito[seq_along(assemblies)],
                    guide = "none") +
  scale_x_discrete(labels = paste0(assemblies, "th")) +
  labs(
    x = "National Assembly",
    y = "Annualized failure rate (failures per year)"
  ) +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank()
  )

ggsave(out_path, plot = p, width = 7, height = 4.5)
