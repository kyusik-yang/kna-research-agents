# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: Women's share and PR share among women across assemblies
library(arrow); library(dplyr); library(ggplot2); library(tidyr)
DATA <- "/Users/kyusik/kna/data/processed"
members <- read_parquet(file.path(DATA, "member_info_17_22.parquet"))
trend <- members |>
  group_by(assembly) |>
  summarise(
    women_share = mean(gender == "여") * 100,
    pr_share_women = mean(election_type == "비례대표" & gender == "여") /
                     mean(gender == "여") * 100,
    .groups = "drop"
  ) |>
  pivot_longer(c(women_share, pr_share_women),
               names_to = "metric", values_to = "value") |>
  mutate(metric = recode(metric,
    women_share = "Women's share of seats",
    pr_share_women = "PR share among women"))
ggplot(trend, aes(x = assembly, y = value, color = metric, shape = metric)) +
  geom_line(linewidth = 0.9) +
  geom_point(size = 2.8) +
  scale_color_manual(values = c("#0072B2", "#D55E00")) +
  scale_x_continuous(breaks = 17:22, labels = paste0(17:22, "th")) +
  labs(x = "National Assembly", y = "Percent",
       color = NULL, shape = NULL) +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom")
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_1.pdf", width = 7, height = 4.2)
