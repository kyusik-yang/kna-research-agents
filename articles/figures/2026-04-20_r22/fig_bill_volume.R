#!/usr/bin/env Rscript
# Figure for R22 article: Monthly member-level bill sponsorship volume
# across the 20th and 21st Assemblies. Real data from master_bills_{20,21}.parquet.

suppressPackageStartupMessages({
  library(arrow); library(dplyr); library(ggplot2); library(lubridate)
})

DATA <- Sys.getenv("KBL_DATA", "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")
OUT  <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-20_r22/fig_bill_volume.pdf"

bills <- bind_rows(
  read_parquet(file.path(DATA, "master_bills_20.parquet")) |>
    select(rst_mona_cd, age, bill_nm, ppsr_kind, ppsl_dt),
  read_parquet(file.path(DATA, "master_bills_21.parquet")) |>
    select(rst_mona_cd, age, bill_nm, ppsr_kind, ppsl_dt)
) |>
  filter(ppsr_kind == "의원", !is.na(ppsl_dt), !is.na(rst_mona_cd)) |>
  mutate(year_month = floor_date(as.Date(ppsl_dt), "month"),
         assembly = factor(age, levels = c(20, 21),
                           labels = c("20th Assembly (2016-2020)", "21st Assembly (2020-2024)")))

monthly <- bills |>
  group_by(assembly, year_month) |>
  summarise(n_bills = n(), n_sponsors = n_distinct(rst_mona_cd), .groups = "drop") |>
  mutate(bills_per_sponsor = n_bills / n_sponsors)

okabe <- c("#0072B2", "#D55E00")

p <- ggplot(monthly, aes(x = year_month, y = bills_per_sponsor, color = assembly)) +
  geom_line(linewidth = 0.45, alpha = 0.9) +
  geom_smooth(method = "loess", span = 0.3, se = FALSE, linewidth = 0.9) +
  scale_color_manual(values = okabe) +
  scale_x_date(date_labels = "%Y-%m", date_breaks = "6 months") +
  labs(x = NULL, y = "Member-bills per active sponsor per month",
       color = NULL) +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        legend.position = "bottom",
        legend.margin = margin(t = -4),
        axis.text.x = element_text(angle = 45, hjust = 1, size = 8),
        plot.margin = margin(6, 10, 4, 6))

dir.create(dirname(OUT), showWarnings = FALSE, recursive = TRUE)
ggsave(OUT, p, width = 7, height = 4.2)
cat("Wrote:", OUT, "\n")
