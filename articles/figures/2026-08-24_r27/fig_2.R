# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: Equivalence bounds for main and placebo estimates
# 90% CIs from the replication pipeline (TOST re-read of frozen fits)
library(ggplot2)
eq <- data.frame(
  test = c("Main DiD", "Placebo DiD"),
  b  = c(-0.86, -0.85),
  lo = c(-2.67, -2.41),
  hi = c(0.96, 0.70))
eq$test <- factor(eq$test, levels = rev(eq$test))
ggplot(eq, aes(x = b, y = test)) +
  geom_vline(xintercept = c(-5, 5), linetype = "dashed",
             colour = "#D55E00") +
  geom_vline(xintercept = c(-2.5, 2.5), linetype = "dotted",
             colour = "#009E73") +
  geom_vline(xintercept = 0, colour = "grey60") +
  geom_pointrange(aes(xmin = lo, xmax = hi), colour = "#0072B2",
                  linewidth = 0.7) +
  labs(x = "Change in ministry share of audit questions (pp, 90% CI)",
       y = NULL) +
  theme_bw(base_size = 11)
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-08-24_r27/fig_2.pdf", width = 7, height = 3)
