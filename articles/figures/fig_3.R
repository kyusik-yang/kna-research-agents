# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 3: Passage rate by gender x mandate type across assemblies
library(arrow); library(dplyr); library(ggplot2); library(tidyr)
DATA <- "/Users/kyusik/kna/data/processed"
members <- read_parquet(file.path(DATA, "member_info_17_22.parquet"))
bills <- bind_rows(lapply(17:22, function(a) {
  f <- file.path(DATA, sprintf("master_bills_%d.parquet", a))
  if (file.exists(f)) read_parquet(f) else NULL
})) |> filter(ppsr_kind == "의원") |>
  mutate(passed = as.integer(passed))
linked <- bills |>
  inner_join(members |> select(mona_cd, assembly, gender, election_type),
             by = c("rst_mona_cd" = "mona_cd", "age" = "assembly"))
agg <- linked |>
  mutate(cell = paste0(
    ifelse(gender == "여", "Women", "Men"), " ",
    ifelse(election_type == "지역구", "SMD", "PR"))) |>
  group_by(age, cell) |>
  summarise(passage = mean(passed, na.rm = TRUE) * 100, .groups = "drop")
ggplot(agg, aes(x = age, y = passage, color = cell, shape = cell)) +
  geom_line(linewidth = 0.9) +
  geom_point(size = 2.8) +
  scale_color_manual(values = c(
    "Men SMD" = "#56B4E9", "Men PR" = "#009E73",
    "Women SMD" = "#D55E00", "Women PR" = "#CC79A7")) +
  scale_x_continuous(breaks = 17:22, labels = paste0(17:22, "th")) +
  labs(x = "National Assembly", y = "Bill passage rate (percent)",
       color = NULL, shape = NULL) +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom")
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_3.pdf", width = 7, height = 4.5)
