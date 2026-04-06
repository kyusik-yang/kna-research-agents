# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 3: Housing bill volume and passage rates across assemblies
library(arrow); library(dplyr); library(ggplot2); library(tidyr)
DATA <- "/Users/kyusik/kna/data/processed"
bills <- bind_rows(lapply(17:22, function(a) {
  f <- file.path(DATA, sprintf("master_bills_%d.parquet", a))
  if (file.exists(f)) read_parquet(f) else NULL
})) |> filter(ppsr_kind == "의원")

housing_kw <- c("부동산","주택","임대","분양","재건축","종합부동산세","양도소득세","다주택","전세","월세","토지")
bills <- bills |> mutate(housing = grepl(paste(housing_kw, collapse="|"), bill_nm))

summary_df <- bills |>
  filter(age %in% 19:22) |>
  group_by(age, housing) |>
  summarise(n = n(), pass_rate = 100 * mean(passed, na.rm=TRUE), .groups="drop") |>
  mutate(
    type = ifelse(housing, "Housing", "Non-Housing"),
    Assembly = paste0(age, "th")
  )

p1 <- ggplot(filter(summary_df, housing), aes(x = Assembly, y = n)) +
  geom_col(fill = "#E69F00", width = 0.6) +
  labs(x = "", y = "Number of Housing Bills") +
  theme_bw(base_size = 11)

p2 <- ggplot(summary_df, aes(x = Assembly, y = pass_rate, color = type, group = type)) +
  geom_line(linewidth = 0.8) +
  geom_point(size = 2.5) +
  scale_color_manual(values = c("Housing" = "#E69F00", "Non-Housing" = "#56B4E9")) +
  labs(x = "", y = "Passage Rate (%)", color = "") +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom")

library(patchwork)
combined <- p1 + p2 + plot_annotation(tag_levels = "a")
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_3.pdf", combined, width = 7, height = 4)
