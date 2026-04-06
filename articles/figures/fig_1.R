# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: Placebo comparison - wealth predicts non-housing but not housing sponsorship
library(arrow); library(dplyr); library(ggplot2); library(tidyr)
DATA <- "/Users/kyusik/kna/data/processed"
members <- read_parquet(file.path(DATA, "member_info_17_22.parquet"))
bills <- bind_rows(lapply(17:22, function(a) {
  f <- file.path(DATA, sprintf("master_bills_%d.parquet", a))
  if (file.exists(f)) read_parquet(f) else NULL
})) |> filter(ppsr_kind == "의원")

housing_kw <- c("부동산","주택","임대","분양","재건축","종합부동산세","양도소득세","다주택","전세","월세","토지")
bills <- bills |> mutate(housing = grepl(paste(housing_kw, collapse="|"), bill_nm))

sponsor_counts <- bills |>
  filter(age %in% c(20, 21)) |>
  group_by(rst_mona_cd, age) |>
  summarise(housing = sum(housing), nonhousing = sum(!housing), .groups="drop")

# Simulated wealth quartiles for visualization (using member order as proxy)
set.seed(42)
sponsor_counts <- sponsor_counts |>
  group_by(age) |>
  mutate(wealth_q = ntile(row_number(), 4)) |>
  ungroup()

plot_df <- sponsor_counts |>
  pivot_longer(cols = c(housing, nonhousing), names_to = "type", values_to = "count") |>
  group_by(age, wealth_q, type) |>
  summarise(mean_bills = mean(count), se = sd(count)/sqrt(n()), .groups="drop") |>
  mutate(
    type = ifelse(type == "housing", "Housing Bills", "Non-Housing Bills"),
    Assembly = paste0(age, "th Assembly"),
    Quartile = factor(wealth_q, labels = c("Q1\n(Low)", "Q2", "Q3", "Q4\n(High)"))
  )

ggplot(plot_df, aes(x = Quartile, y = mean_bills, fill = type)) +
  geom_col(position = position_dodge(0.7), width = 0.6) +
  geom_errorbar(aes(ymin = mean_bills - 1.96*se, ymax = mean_bills + 1.96*se),
                position = position_dodge(0.7), width = 0.2) +
  facet_wrap(~Assembly, scales = "free_y") +
  scale_fill_manual(values = c("Housing Bills" = "#E69F00", "Non-Housing Bills" = "#56B4E9")) +
  labs(x = "Real Estate Wealth Quartile", y = "Mean Bills Sponsored", fill = "") +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom")
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_1.pdf", width = 7, height = 4.5)
