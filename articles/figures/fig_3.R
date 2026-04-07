# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 3: Special Counsel Bill Trends and Passage in 22nd Assembly
library(arrow); library(dplyr); library(ggplot2); library(lubridate)
DATA <- "/Users/kyusik/kna/data/processed"
bills22 <- read_parquet(file.path(DATA, "master_bills_22.parquet"))
inv_kw <- c("특별검사", "특검", "탄핵", "내란", "국정조사", "비상계엄", "계엄")
bills22 <- bills22 |>
  mutate(
    propose_date = as.Date(ppsl_dt),
    propose_month = floor_date(propose_date, "month"),
    is_investigation = grepl(paste(inv_kw, collapse = "|"), bill_nm, perl = TRUE),
    bill_type = ifelse(is_investigation, "Investigation", "Routine")
  )
monthly_type <- bills22 |>
  filter(!is.na(propose_month)) |>
  group_by(propose_month, bill_type) |>
  summarise(n = n(), .groups = "drop")
okabe_ito <- c("#0072B2", "#D55E00")
ggplot(monthly_type, aes(x = propose_month, y = n, fill = bill_type)) +
  geom_col(width = 25) +
  scale_fill_manual(values = okabe_ito, name = "") +
  labs(x = "", y = "Bills Introduced") +
  theme_bw(base_size = 11) +
  theme(legend.position = "top")
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_3.pdf", width = 7, height = 4.5)
