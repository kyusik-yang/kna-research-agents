# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 3: Bunching of beopsawi dwell times around 60-day threshold
library(arrow); library(dplyr); library(ggplot2)
DATA <- "/Users/kyusik/kna/data/processed"
bills22 <- read_parquet(file.path(DATA, "master_bills_22.parquet"))
bills22 <- bills22 |>
  filter(bill_kind == "법률안") |>
  mutate(
    jrcmit_in_d = as.Date(jrcmit_prsnt_dt),
    jrcmit_out_d = as.Date(jrcmit_proc_dt),
    dwell = as.numeric(jrcmit_out_d - jrcmit_in_d)
  ) |>
  filter(!is.na(dwell), dwell >= 0, dwell <= 150)
ggplot(bills22, aes(x = dwell)) +
  geom_histogram(binwidth = 5, fill = "#56B4E9",
                 color = "white", boundary = 0) +
  geom_vline(xintercept = 60, linetype = "dashed",
             color = "#D55E00", size = 0.8) +
  annotate("text", x = 70, y = Inf, vjust = 1.5,
           label = "60-day threshold\n(Art. 86(3))", size = 3.2,
           color = "#D55E00") +
  scale_x_continuous(breaks = seq(0, 150, 15)) +
  labs(x = "Days held by Legislation and Judiciary Committee",
       y = "Number of bills (22nd Assembly)") +
  theme_bw(base_size = 11)
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_3.pdf", width = 7, height = 4.5)
