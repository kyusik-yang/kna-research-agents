# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: Cross-Committee Change in Prosecutorial Keyword Share
library(arrow); library(dplyr); library(ggplot2); library(tidyr)
DATA <- "/Users/kyusik/kna/data/processed"
bills <- bind_rows(lapply(17:22, function(a) {
  f <- file.path(DATA, sprintf("master_bills_%d.parquet", a))
  if (file.exists(f)) read_parquet(f) else NULL
}))
sp_bills <- bills |>
  filter(grepl("특별검사|특검", bill_nm, perl = TRUE)) |>
  mutate(assembly = as.factor(age))
sp_summary <- sp_bills |>
  group_by(age) |>
  summarise(
    total = n(),
    passed = sum(passed == TRUE, na.rm = TRUE),
    .groups = "drop"
  ) |>
  pivot_longer(cols = c(total, passed), names_to = "type", values_to = "count") |>
  mutate(
    type = factor(type, levels = c("total", "passed"),
                  labels = c("Introduced", "Passed")),
    age = factor(age)
  )
okabe_ito <- c("#0072B2", "#D55E00")
ggplot(sp_summary, aes(x = age, y = count, fill = type)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.6) +
  scale_fill_manual(values = okabe_ito, name = "") +
  labs(x = "Assembly", y = "Number of Special Counsel Bills") +
  theme_bw(base_size = 11) +
  theme(legend.position = "top")
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_1.pdf", width = 7, height = 4.5)
