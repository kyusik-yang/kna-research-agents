#!/usr/bin/env Rscript
# Figure 3: Monthly Bill Introductions by Type, 22nd Assembly
# Fix from previous run: avoid cairo_pdf (libSM/libXrender missing on this machine).
# Use the base R "pdf" device explicitly via ggsave(device = "pdf").

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

# ---- Paths ------------------------------------------------------------------
data_dir <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
bills_path <- file.path(data_dir, "master_bills_22.parquet")
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-06_r10/fig_3.pdf"

dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)

# ---- Load 22nd Assembly bills ----------------------------------------------
bills22 <- arrow::read_parquet(
  bills_path,
  col_select = c("bill_id", "bill_nm", "ppsl_dt")
) %>%
  as_tibble()

# Investigation-related keywords from paper
inv_keywords <- c(
  "\ud2b9\ubcc4\uac80\uc0ac",   # 특별검사
  "\ud2b9\uac80",               # 특검
  "\ud0c4\ud575",               # 탄핵
  "\ub0b4\ub780",               # 내란
  "\uad6d\uc815\uc870\uc0ac",   # 국정조사
  "\ube44\uc0c1\uacc4\uc5c4",   # 비상계엄
  "\uacc4\uc5c4"                # 계엄
)
inv_pattern <- paste(inv_keywords, collapse = "|")

bills22 <- bills22 %>%
  mutate(
    bill_nm = ifelse(is.na(bill_nm), "", as.character(bill_nm)),
    is_investigation = grepl(inv_pattern, bill_nm),
    ppsl_dt = suppressWarnings(as.Date(ppsl_dt))
  ) %>%
  filter(!is.na(ppsl_dt))

total_n <- nrow(bills22)
inv_n <- sum(bills22$is_investigation)
cat(sprintf("22nd Assembly: %d total bills, %d investigation-related (%.2f%%)\n",
            total_n, inv_n, 100 * inv_n / total_n))

# ---- Aggregate by month -----------------------------------------------------
monthly <- bills22 %>%
  mutate(month = as.Date(format(ppsl_dt, "%Y-%m-01"))) %>%
  group_by(month) %>%
  summarise(
    Investigation = sum(is_investigation),
    Routine = sum(!is_investigation),
    .groups = "drop"
  ) %>%
  arrange(month) %>%
  pivot_longer(cols = c("Routine", "Investigation"),
               names_to = "Bill type", values_to = "n") %>%
  mutate(`Bill type` = factor(`Bill type`, levels = c("Routine", "Investigation")))

# ---- Plot -------------------------------------------------------------------
okabe_ito <- c("Routine" = "#56B4E9", "Investigation" = "#D55E00")

p <- ggplot(monthly, aes(x = month, y = n, fill = `Bill type`)) +
  geom_col(width = 25, color = NA) +
  scale_fill_manual(values = okabe_ito) +
  scale_x_date(date_breaks = "3 months", date_labels = "%Y-%m") +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  labs(x = NULL, y = "Bills introduced", fill = NULL) +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "top",
    legend.margin = margin(0, 0, 0, 0),
    panel.grid.minor = element_blank(),
    axis.text.x = element_text(angle = 45, hjust = 1)
  )

# ---- Save (non-cairo to avoid libSM/libXrender) -----------------------------
ggsave(out_path, plot = p, width = 7, height = 4.5, device = "pdf",
       useDingbats = FALSE)

cat(sprintf("Saved: %s\n", out_path))
