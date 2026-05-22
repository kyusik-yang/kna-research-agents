# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: Bypass share trend across assemblies
library(arrow); library(dplyr); library(ggplot2)
DATA <- "/Users/kyusik/kna/data/processed"
bills <- bind_rows(lapply(17:22, function(a) {
  f <- file.path(DATA, sprintf("master_bills_%d.parquet", a))
  if (file.exists(f)) {
    df <- read_parquet(f)
    df$assembly <- a
    df
  } else NULL
}))
bills <- bills |>
  filter(bill_kind == "법률안") |>
  mutate(
    is_alt = grepl("대안", bill_nm),
    skipped_jrcmit = is.na(jrcmit_prsnt_dt),
    reached_plenary = !is.na(rgs_prsnt_dt)
  )
summary_df <- bills |>
  filter(reached_plenary) |>
  group_by(assembly) |>
  summarise(
    plenary_bills = n(),
    bypass = sum(is_alt & skipped_jrcmit, na.rm = TRUE),
    bypass_share = 100 * bypass / plenary_bills
  )
ggplot(summary_df, aes(x = assembly, y = bypass_share)) +
  geom_line(color = "#0072B2", size = 1.1) +
  geom_point(size = 3.5, color = "#0072B2") +
  scale_x_continuous(breaks = 17:22,
    labels = c("17th\n(1996)","18th\n(2008)","19th\n(2012)",
               "20th\n(2016)","21st\n(2020)","22nd\n(2024)")) +
  scale_y_continuous(limits = c(0, 60), breaks = seq(0, 60, 10)) +
  labs(x = "Assembly (start year)",
       y = "Share of plenary bills via committee-alternative bypass (%)") +
  theme_bw(base_size = 11)
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_1.pdf", width = 7, height = 4.5)
