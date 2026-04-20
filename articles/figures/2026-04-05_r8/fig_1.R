#!/usr/bin/env Rscript
# Figure 1, r8: Wealth quartile vs sponsorship counts (housing vs non-housing)
# Data: master_bills_{21,22}.parquet + assets_wealth_panel.parquet
# All numbers computed at runtime from public KNA parquets. No hardcoding.

suppressPackageStartupMessages({
  library(arrow); library(dplyr); library(ggplot2); library(stringr); library(tidyr)
})

DATA <- Sys.getenv("KBL_DATA", "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")
OUT  <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-05_r8/fig_1.pdf"

# Housing/real estate keywords for bill_nm classification
housing_kw <- "주택|부동산|임대|전세|월세|재건축|재개발|종합부동산세|종부세|양도소득세|아파트|분양"

# Combine 21st (full) + 22nd (in-progress) member-bill cohorts
bills <- bind_rows(
  read_parquet(file.path(DATA, "master_bills_21.parquet")) |>
    select(rst_mona_cd, age, bill_nm, ppsr_kind),
  read_parquet(file.path(DATA, "master_bills_22.parquet")) |>
    select(rst_mona_cd, age, bill_nm, ppsr_kind)
) |>
  filter(ppsr_kind == "의원", !is.na(rst_mona_cd), nchar(rst_mona_cd) > 0) |>
  mutate(housing = str_detect(bill_nm, housing_kw))

# Per-legislator counts of housing vs non-housing bills
sponsor_counts <- bills |>
  group_by(rst_mona_cd, age) |>
  summarise(housing_bills = sum(housing),
            nonhousing_bills = sum(!housing), .groups = "drop")

# Wealth panel: latest year per (mona_cd, assembly)
wealth <- read_parquet(file.path(DATA, "assets_wealth_panel.parquet")) |>
  filter(assembly %in% c(21, 22), !is.na(total_realestate_q)) |>
  group_by(mona_cd, assembly) |>
  slice_max(wealth_year, n = 1, with_ties = FALSE) |>
  ungroup() |>
  select(mona_cd, assembly, total_realestate_q)

# Join: wealth.mona_cd matches bills.rst_mona_cd, wealth.assembly matches bills.age
joined <- wealth |>
  left_join(sponsor_counts, by = c("mona_cd" = "rst_mona_cd", "assembly" = "age")) |>
  mutate(housing_bills    = coalesce(housing_bills, 0L),
         nonhousing_bills = coalesce(nonhousing_bills, 0L))

# Quartile order (Q1 = lowest real estate wealth)
joined <- joined |>
  mutate(quartile = factor(total_realestate_q, levels = c("Q1","Q2","Q3","Q4")))

# Mean per legislator with 95% CI (normal approximation)
agg <- joined |>
  pivot_longer(c(housing_bills, nonhousing_bills),
               names_to = "category", values_to = "n_bills") |>
  mutate(category = recode(category,
                           housing_bills    = "Housing-related bills",
                           nonhousing_bills = "Non-housing bills")) |>
  group_by(quartile, category) |>
  summarise(mean = mean(n_bills),
            se   = sd(n_bills) / sqrt(n()),
            lo   = mean - 1.96 * se,
            hi   = mean + 1.96 * se,
            n    = n(), .groups = "drop")

okabe <- c("#0072B2", "#D55E00")

p <- ggplot(agg, aes(x = quartile, y = mean, fill = category)) +
  geom_col(position = position_dodge(width = 0.78), width = 0.7,
           colour = "grey20", linewidth = 0.25) +
  geom_errorbar(aes(ymin = pmax(0, lo), ymax = hi),
                position = position_dodge(width = 0.78), width = 0.18,
                colour = "grey20", linewidth = 0.4) +
  scale_fill_manual(values = okabe) +
  labs(x = "Real-estate wealth quartile (Q1 = lowest)",
       y = "Mean bills sponsored per legislator (21st-22nd Assemblies)",
       fill = NULL) +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        panel.grid.major.x = element_blank(),
        legend.position = "bottom",
        legend.margin = margin(t = -4),
        plot.margin = margin(6, 10, 4, 6))

dir.create(dirname(OUT), showWarnings = FALSE, recursive = TRUE)
ggsave(OUT, p, width = 7, height = 4.5)
cat("Wrote:", OUT, "\n")
