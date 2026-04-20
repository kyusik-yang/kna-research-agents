# Figure 2: Monthly Bill Passage in the 20th Assembly, June 2016 - May 2020
# Reads master_bills_20.parquet and counts bills passed by month based on cmt_proc_dt.
# Uses base R pdf device (not cairo) to avoid X11/cairo loader errors.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

okabe_ito <- c("#E69F00","#56B4E9","#009E73","#0072B2",
               "#D55E00","#CC79A7","#000000")

data_dir <- Sys.getenv("KBL_DATA",
  unset = "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")
bills_path <- file.path(data_dir, "master_bills_20.parquet")
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-06_r10/fig_2.pdf"

bills <- arrow::read_parquet(bills_path)

# Identify a usable date column for "passage" timing.
# Prefer cmt_proc_dt (committee processing); fall back to law_proc_dt or ppsl_dt.
candidate_cols <- c("cmt_proc_dt", "law_proc_dt", "ppsl_dt")
date_col <- candidate_cols[candidate_cols %in% names(bills)][1]

bills <- bills %>%
  mutate(
    passed_flag = suppressWarnings(as.integer(passed)),
    date_val = suppressWarnings(as.Date(.data[[date_col]]))
  ) %>%
  filter(!is.na(passed_flag), passed_flag == 1L,
         !is.na(date_val),
         date_val >= as.Date("2016-06-01"),
         date_val <= as.Date("2020-05-31"))

# Build the full month grid for the 20th Assembly window.
months <- seq(as.Date("2016-06-01"), as.Date("2020-05-01"), by = "month")
month_grid <- tibble(month = months)

monthly <- bills %>%
  mutate(month = as.Date(format(date_val, "%Y-%m-01"))) %>%
  count(month, name = "n_passed")

monthly <- month_grid %>%
  left_join(monthly, by = "month") %>%
  mutate(n_passed = tidyr::replace_na(n_passed, 0L))

# Investigation period: 박근혜 국정조사 was activated late November 2016
# through early 2017. Shade Nov 2016 - Mar 2017 as the reference window.
inv_start <- as.Date("2016-11-01")
inv_end   <- as.Date("2017-03-31")

p <- ggplot(monthly, aes(x = month, y = n_passed)) +
  annotate("rect",
           xmin = inv_start, xmax = inv_end,
           ymin = -Inf, ymax = Inf,
           fill = okabe_ito[2], alpha = 0.18) +
  annotate("text",
           x = inv_start + (inv_end - inv_start)/2,
           y = max(monthly$n_passed, na.rm = TRUE) * 0.96,
           label = "Investigation\nperiod",
           size = 3, color = okabe_ito[4], hjust = 0.5, vjust = 1) +
  geom_col(fill = okabe_ito[7], width = 25, alpha = 0.85) +
  geom_smooth(method = "loess", span = 0.35, se = FALSE,
              color = okabe_ito[5], linewidth = 0.7,
              formula = y ~ x) +
  scale_x_date(date_breaks = "6 months", date_labels = "%Y-%m",
               expand = expansion(mult = c(0.01, 0.01))) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.06))) +
  labs(x = NULL, y = "Bills passed (per month)") +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.text.x = element_text(angle = 30, hjust = 1)
  )

dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)

# Use base R pdf device to bypass cairo loader issues on this machine.
ggsave(out_path, plot = p, width = 7, height = 4.5, device = "pdf")
