# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 3: within-opposition dose slopes vs the diluted-continuity bar
library(ggplot2)
d <- data.frame(
  spec = c("Cohort 1", "Pooled", "Log dose",
           "Excl. single-ministry committee", "Placebo outcome"),
  est = c(1.78, 1.28, 1.34, 1.10, 0.21),
  lo  = c(-0.11, -0.14, 0.07, -0.39, -1.04),
  hi  = c( 3.68,  2.69, 2.62,  2.58,  1.47)
)
d$spec <- factor(d$spec, levels = rev(d$spec))
ggplot(d, aes(x = est, y = spec)) +
  geom_vline(xintercept = 0, colour = "grey55") +
  geom_vline(xintercept = 2.5, linetype = "dashed", colour = "#D55E00") +
  geom_errorbarh(aes(xmin = lo, xmax = hi), height = 0.16,
                 colour = "#0072B2") +
  geom_point(size = 2.4, colour = "#0072B2") +
  annotate("text", x = 2.5, y = 0.6, label = "diluted-continuity bar",
           hjust = -0.05, vjust = 0, size = 3, colour = "#D55E00") +
  labs(x = "Slope of audit reallocation on hearing dose (pp per SD)",
       y = NULL) +
  theme_bw(base_size = 11)
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-08-24_r27/fig_3.pdf", width = 7, height = 4.0)
