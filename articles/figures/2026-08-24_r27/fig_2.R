# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: decomposition of the baseline levels gap
library(ggplot2)
d <- data.frame(
  spec = c("Raw gap (cohort 1)",
           "Excl. single-ministry committee (raw)",
           "Committee FE (cohort 1)",
           "Committee FE (pooled)",
           "Placebo agencies (pooled, FE)"),
  est = c(4.61, 0.61, 0.69, 1.53, 2.23),
  lo  = c(NA,   NA,  -0.99, -0.05, 0.18),
  hi  = c(NA,   NA,   2.37,  3.11, 4.28)
)
d$spec <- factor(d$spec, levels = rev(d$spec))
ggplot(d, aes(x = est, y = spec)) +
  geom_vline(xintercept = 0, colour = "grey55") +
  geom_errorbarh(aes(xmin = lo, xmax = hi), height = 0.16,
                 colour = "#0072B2", na.rm = TRUE) +
  geom_point(size = 2.4, colour = "#0072B2") +
  labs(x = "Pre-hearing gap in ministry share, opposed vs supportive (pp)",
       y = NULL) +
  theme_bw(base_size = 11)
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-08-24_r27/fig_2.pdf", width = 7, height = 4.0)
