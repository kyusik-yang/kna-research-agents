#!/usr/bin/env Rscript
# Figure 2: Rising Absorption Ratio - Individual Bills per Chair Alternative,
# 17th-22nd Korean National Assemblies.
#
# Data source: master_bills_{17-22}.parquet
#   - Chair alternatives: ppsr_kind == "위원장"
#   - Absorbed bills:     cmt_proc_result_cd == "대안반영폐기"
# Absorption ratio = (# absorbed bills) / (# chair alternatives) per assembly.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

# ---- 1. Locate data directory ------------------------------------------------
data_dir <- Sys.getenv("KBL_DATA", unset = "")
if (!nzchar(data_dir) || !dir.exists(data_dir)) {
  data_dir <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
}

assemblies <- 17:22

# ---- 2. Compute counts per assembly -----------------------------------------
compute_counts <- function(age) {
  path <- file.path(data_dir, sprintf("master_bills_%d.parquet", age))
  df <- arrow::read_parquet(
    path,
    col_select = c("bill_id", "ppsr_kind", "cmt_proc_result_cd")
  )
  chair_bills <- sum(df$ppsr_kind == "위원장", na.rm = TRUE)
  absorbed    <- sum(df$cmt_proc_result_cd == "대안반영폐기", na.rm = TRUE)
  tibble::tibble(
    assembly      = age,
    chair_bills   = chair_bills,
    absorbed      = absorbed,
    ratio         = ifelse(chair_bills > 0, absorbed / chair_bills, NA_real_)
  )
}

res <- bind_rows(lapply(assemblies, compute_counts))

# ---- 3. Plot -----------------------------------------------------------------
okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#000000")

assembly_labels <- c("17th\n(2004-08)", "18th\n(2008-12)",
                     "19th\n(2012-16)", "20th\n(2016-20)",
                     "21st\n(2020-24)", "22nd\n(2024-)")

res_plot <- res %>%
  mutate(
    assembly_label = factor(assembly_labels[assembly - 16],
                            levels = assembly_labels),
    label_text     = sprintf("%.1f", ratio)
  )

p <- ggplot(res_plot, aes(x = assembly_label, y = ratio, group = 1)) +
  geom_line(color = okabe_ito[4], linewidth = 0.9) +
  geom_point(color = okabe_ito[5], size = 3.2) +
  geom_text(aes(label = label_text),
            vjust = -1.1, size = 3.4, color = "grey20") +
  scale_y_continuous(
    limits = c(0, max(res_plot$ratio, na.rm = TRUE) * 1.20),
    breaks = seq(0, 6, by = 1),
    expand = expansion(mult = c(0, 0.02))
  ) +
  labs(
    x = "Assembly",
    y = "Bills absorbed per chair alternative"
  ) +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title.x = element_text(margin = margin(t = 6)),
    axis.title.y = element_text(margin = margin(r = 6)),
    plot.margin = margin(8, 10, 6, 8)
  )

# ---- 4. Save -----------------------------------------------------------------
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-08_r11/fig_2.pdf"
dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)
ggsave(out_path, plot = p, width = 7, height = 4.5)

invisible(res)
