# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: Per-capita bill sponsorship by gender across assemblies
library(arrow); library(dplyr); library(ggplot2)
DATA <- "/Users/kyusik/kna/data/processed"
members <- read_parquet(file.path(DATA, "member_info_17_22.parquet"))
bills <- bind_rows(lapply(17:22, function(a) {
  f <- file.path(DATA, sprintf("master_bills_%d.parquet", a))
  if (file.exists(f)) read_parquet(f) else NULL
})) |> filter(ppsr_kind == "의원")
counts <- bills |>
  group_by(assembly = age, mona_cd = rst_mona_cd) |>
  summarise(n_bills = n(), .groups = "drop")
joined <- members |>
  left_join(counts, by = c("assembly", "mona_cd")) |>
  mutate(n_bills = ifelse(is.na(n_bills), 0, n_bills))
agg <- joined |>
  group_by(assembly, gender) |>
  summarise(mean_bills = mean(n_bills), .groups = "drop") |>
  mutate(gender = recode(gender, "여" = "Women", "남" = "Men"))
ggplot(agg, aes(x = assembly, y = mean_bills, color = gender, shape = gender)) +
  geom_line(linewidth = 0.9) +
  geom_point(size = 2.8) +
  scale_color_manual(values = c("Men" = "#56B4E9", "Women" = "#D55E00")) +
  scale_x_continuous(breaks = 17:22, labels = paste0(17:22, "th")) +
  labs(x = "National Assembly", y = "Bills sponsored per legislator",
       color = NULL, shape = NULL) +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom")
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_2.pdf", width = 7, height = 4.2)
