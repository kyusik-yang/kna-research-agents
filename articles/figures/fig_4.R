# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 4: Gender-keyword bill share over time
library(arrow); library(dplyr); library(ggplot2); library(stringr)
DATA <- "/Users/kyusik/kna/data/processed"
bills <- bind_rows(lapply(17:22, function(a) {
  f <- file.path(DATA, sprintf("master_bills_%d.parquet", a))
  if (file.exists(f)) read_parquet(f) else NULL
})) |> filter(ppsr_kind == "의원")
keywords <- "성평등|여성|양성평등|성차별|성폭력|성희롱"
agg <- bills |>
  mutate(gender_bill = str_detect(replace_na(bill_name, ""), keywords)) |>
  group_by(age) |>
  summarise(share = mean(gender_bill) * 100, .groups = "drop")
ggplot(agg, aes(x = age, y = share)) +
  geom_line(linewidth = 0.9, color = "#0072B2") +
  geom_point(size = 2.8, color = "#0072B2") +
  scale_x_continuous(breaks = 17:22, labels = paste0(17:22, "th")) +
  labs(x = "National Assembly",
       y = "Share of bills with gender keywords (percent)") +
  theme_bw(base_size = 11)
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_4.pdf", width = 7, height = 4.2)
