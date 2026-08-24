# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: coefficient plot of DiD estimates vs the preregistered threshold
library(ggplot2)
d <- data.frame(
  spec = c("Pooled DiD", "Cohort 1 (2020-2021)", "Cohort 2 (2023)",
           "Government-change cohort", "Own-speech coding",
           "Placebo agencies"),
  est = c(-0.86, -1.10, 1.30, 0.09, -1.60, -0.85),
  lo  = c(-3.01, -3.60, -3.50, -3.80, -4.80, -2.70),
  hi  = c( 1.30,  1.40,  6.00,  3.99,  1.70,  1.00)
)
d$spec <- factor(d$spec, levels = rev(d$spec))
ggplot(d, aes(x = est, y = spec)) +
  geom_vline(xintercept = 0, colour = "grey55") +
  geom_vline(xintercept = 5, linetype = "dashed", colour = "#D55E00") +
  geom_errorbarh(aes(xmin = lo, xmax = hi), height = 0.16,
                 colour = "#0072B2") +
  geom_point(size = 2.4, colour = "#0072B2") +
  annotate("text", x = 5, y = 0.6, label = "preregistered threshold",
           hjust = 1.05, vjust = 0, size = 3, colour = "#D55E00") +
  labs(x = "Change in confirmed-ministry share of audit questions (pp)",
       y = NULL) +
  theme_bw(base_size = 11)
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-08-24_r27/fig_1.pdf", width = 7, height = 4.5)
