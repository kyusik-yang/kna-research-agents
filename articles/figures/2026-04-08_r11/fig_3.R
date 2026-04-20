#!/usr/bin/env Rscript
# Figure 3: Floor Rejections (부결) by Assembly, 17th-22nd
# Fix vs previous attempt: default PDF device on macOS tries to use cairo,
# which requires XQuartz (libSM/libXrender). We force device = "pdf" (base
# grDevices::pdf) which does not need cairo/X11.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
out_pdf  <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-08_r11/fig_3.pdf"

# Load all 6 assemblies, keep only columns we need
assemblies <- 17:22
read_one <- function(a) {
  f <- file.path(data_dir, sprintf("master_bills_%d.parquet", a))
  read_parquet(f, col_select = c("bill_id", "age", "law_proc_rslt", "cmt_proc_result_cd", "passed"))
}
bills <- bind_rows(lapply(assemblies, read_one))

# Identify rejection at plenary floor.
# law_proc_rslt holds the final plenary outcome string; "부결" = rejected.
bills <- bills %>%
  mutate(
    lpr = ifelse(is.na(law_proc_rslt), "", as.character(law_proc_rslt)),
    rejected = grepl("부결", lpr),
    # "plenary-reached" = any final-stage outcome recorded in law_proc_rslt
    reached_floor = nzchar(lpr)
  )

rej_tbl <- bills %>%
  group_by(age) %>%
  summarise(
    n_rejected     = sum(rejected, na.rm = TRUE),
    n_floor        = sum(reached_floor, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    assembly_lbl = paste0(age, "th"),
    rate_pct = ifelse(n_floor > 0, 100 * n_rejected / n_floor, NA_real_)
  ) %>%
  arrange(age)

# Okabe-Ito
okabe <- c("#E69F00","#56B4E9","#009E73","#0072B2","#D55E00","#CC79A7","#000000")

p <- ggplot(rej_tbl, aes(x = factor(age), y = n_rejected)) +
  geom_col(fill = okabe[4], width = 0.65) +
  geom_text(aes(label = n_rejected), vjust = -0.5, size = 3.3) +
  scale_x_discrete(labels = function(x) paste0(x, "th")) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.15))) +
  labs(x = "Assembly", y = "Number of bills rejected (부결) on the floor") +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank()
  )

# Use base pdf device to avoid cairo dependency on macOS
ggsave(out_pdf, plot = p, width = 7, height = 4.5, device = "pdf")
