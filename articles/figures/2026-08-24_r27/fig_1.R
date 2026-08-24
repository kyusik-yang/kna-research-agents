# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: DiD estimates across samples and specifications
# Estimates (pp, 95% CI) from the replication pipeline
# (workspace/r25-r27 consolidation rerun)
library(ggplot2); library(dplyr)
est <- data.frame(
  spec = c("Pooled", "Cohort 1 (2020-21)", "Cohort 2 (2023)",
           "Cohort 3 (2022, govt change)", "Own-speech coding",
           "Placebo agencies"),
  b  = c(-0.86, -1.10, 1.30, 0.09, -1.60, -0.85),
  lo = c(-3.01, -3.60, -3.50, -3.80, -4.80, -2.70),
  hi = c(1.30, 1.40, 6.00, 3.99, 1.70, 1.00))
est$spec <- factor(est$spec, levels = rev(est$spec))
ggplot(est, aes(x = b, y = spec)) +
  geom_vline(xintercept = 0, linetype = "dashed", colour = "grey50") +
  geom_vline(xintercept = c(-5, 5), linetype = "dotted",
             colour = "#D55E00") +
  geom_pointrange(aes(xmin = lo, xmax = hi), colour = "#0072B2",
                  linewidth = 0.6) +
  labs(x = "Change in confirmed-ministry share of audit questions (pp)",
       y = NULL) +
  theme_bw(base_size = 11)
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-08-24_r27/fig_1.pdf", width = 7, height = 4.5)
