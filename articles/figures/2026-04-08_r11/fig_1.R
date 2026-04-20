#!/usr/bin/env Rscript
# Figure 1, r11: Legislative Funnel by Sponsor Bloc, 22nd Assembly (2024-2026)
# Data: master_bills_22.parquet + members_22.parquet
# All numbers computed at runtime from KNA parquets. No hardcoding.

suppressPackageStartupMessages({
  library(arrow); library(dplyr); library(ggplot2); library(tidyr); library(stringr)
})

DATA <- Sys.getenv("KBL_DATA", "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")
OUT  <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-08_r11/fig_1.pdf"

bills <- read_parquet(file.path(DATA, "master_bills_22.parquet")) |>
  filter(ppsr_kind == "의원", !is.na(rst_mona_cd), nchar(rst_mona_cd) > 0)

members <- read_parquet(file.path(DATA, "members_22.parquet")) |>
  select(mona_cd, party)

bloc <- function(p) {
  case_when(
    str_detect(p, "더불어민주|민주당") ~ "DPK (ruling)",
    str_detect(p, "국민의힘|국민의 힘") ~ "PPP (opposition)",
    TRUE ~ "Other / minor"
  )
}

joined <- bills |>
  left_join(members, by = c("rst_mona_cd" = "mona_cd")) |>
  mutate(bloc = bloc(party))

stages <- joined |>
  group_by(bloc) |>
  summarise(introduced = n(),
            referred   = sum(!is.na(committee_dt)),
            processed  = sum(!is.na(cmt_proc_dt)),
            passed     = sum(passed == 1, na.rm = TRUE), .groups = "drop") |>
  pivot_longer(-bloc, names_to = "stage", values_to = "n") |>
  mutate(stage = factor(stage,
                        levels = c("introduced", "referred", "processed", "passed"),
                        labels = c("Introduced", "Referred to committee",
                                   "Processed by committee", "Passed plenary")))

stages <- stages |>
  group_by(bloc) |>
  mutate(share = n / n[stage == "Introduced"]) |>
  ungroup()

okabe <- c("DPK (ruling)" = "#0072B2",
           "PPP (opposition)" = "#D55E00",
           "Other / minor" = "#999999")

p <- ggplot(stages, aes(x = stage, y = share, fill = bloc)) +
  geom_col(position = position_dodge(width = 0.8), width = 0.72,
           colour = "grey20", linewidth = 0.25) +
  geom_text(aes(label = scales::comma(n)),
            position = position_dodge(width = 0.8),
            vjust = -0.4, size = 2.8, colour = "grey25") +
  scale_y_continuous(labels = scales::percent_format(accuracy = 1),
                     limits = c(0, 1.05), expand = expansion(mult = c(0, 0.02))) +
  scale_fill_manual(values = okabe) +
  labs(x = NULL, y = "Share of bloc's bills surviving stage",
       fill = NULL) +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        panel.grid.major.x = element_blank(),
        legend.position = "bottom",
        legend.margin = margin(t = -4),
        plot.margin = margin(6, 10, 4, 6))

dir.create(dirname(OUT), showWarnings = FALSE, recursive = TRUE)
ggsave(OUT, p, width = 7, height = 4.5)
cat("Wrote:", OUT, "\n")
