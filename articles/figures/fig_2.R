# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: Monthly Bill Passage in the 20th Assembly
library(arrow); library(dplyr); library(ggplot2); library(lubridate)
DATA <- "/Users/kyusik/kna/data/processed"
bills20 <- read_parquet(file.path(DATA, "master_bills_20.parquet"))
bills20 <- bills20 |>
  mutate(proc_date = as.Date(proc_dt),
         proc_month = floor_date(proc_date, "month"),
         is_passed = (passed == TRUE))
monthly <- bills20 |>
  filter(!is.na(proc_month), proc_month >= as.Date("2016-06-01"),
         proc_month <= as.Date("2020-05-01")) |>
  group_by(proc_month) |>
  summarise(passed = sum(is_passed, na.rm = TRUE), .groups = "drop")
okabe_ito <- c("#0072B2", "#D55E00", "#009E73")
ggplot(monthly, aes(x = proc_month, y = passed)) +
  geom_line(color = okabe_ito[1], linewidth = 0.6) +
  geom_point(color = okabe_ito[1], size = 1.5) +
  geom_vline(xintercept = as.Date("2016-10-25"), linetype = "dashed",
             color = okabe_ito[2], linewidth = 0.5) +
  annotate("text", x = as.Date("2016-10-25"), y = max(monthly$passed, na.rm=TRUE)*0.95,
           label = "Scandal erupts", hjust = -0.1, size = 3, color = okabe_ito[2]) +
  geom_vline(xintercept = as.Date("2016-12-09"), linetype = "dotted",
             color = okabe_ito[3], linewidth = 0.5) +
  annotate("text", x = as.Date("2016-12-09"), y = max(monthly$passed, na.rm=TRUE)*0.85,
           label = "Impeachment vote", hjust = -0.1, size = 3, color = okabe_ito[3]) +
  labs(x = "", y = "Bills Passed") +
  theme_bw(base_size = 11)
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_2.pdf", width = 7, height = 4.5)
