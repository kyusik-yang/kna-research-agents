# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: Ideology vs. housing sponsorship rate by assembly
library(arrow); library(dplyr); library(ggplot2)
DATA <- "/Users/kyusik/kna/data/processed"
members <- read_parquet(file.path(DATA, "member_info_17_22.parquet"))
bills <- bind_rows(lapply(17:22, function(a) {
  f <- file.path(DATA, sprintf("master_bills_%d.parquet", a))
  if (file.exists(f)) read_parquet(f) else NULL
})) |> filter(ppsr_kind == "의원")
dw <- read.csv(file.path(DATA, "dw_ideal_points_20_22.csv"))

housing_kw <- c("부동산","주택","임대","분양","재건축","종합부동산세","양도소득세","다주택","전세","월세","토지")
bills <- bills |> mutate(housing = grepl(paste(housing_kw, collapse="|"), bill_nm))

sponsor_rates <- bills |>
  filter(age %in% c(20, 21, 22)) |>
  group_by(rst_mona_cd, age) |>
  summarise(housing_pct = 100 * mean(housing), total = n(), .groups="drop") |>
  filter(total >= 5)

merged <- inner_join(sponsor_rates, dw, by = c("rst_mona_cd" = "mona_cd", "age" = "assembly"))

ggplot(merged, aes(x = coord1D, y = housing_pct)) +
  geom_point(alpha = 0.3, size = 1.5, color = "#0072B2") +
  geom_smooth(method = "lm", se = TRUE, color = "#D55E00", linewidth = 0.8) +
  facet_wrap(~paste0(age, "th Assembly"), scales = "free") +
  labs(x = "DW-NOMINATE (1st Dimension)", y = "Housing Bills (% of Total)") +
  theme_bw(base_size = 11)
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_2.pdf", width = 7, height = 4.5)
