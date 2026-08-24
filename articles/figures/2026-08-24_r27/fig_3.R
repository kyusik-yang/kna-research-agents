# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 3: Within-opposition dose slopes across specifications
# Estimates (pp per SD or per unit, 95% CI) from replication pipeline
library(ggplot2)
dose <- data.frame(
  spec = c("Standardized dose, pooled", "Standardized dose, cohort 1",
           "Log dose, pooled", "Excl. single-ministry committee",
           "Placebo outcome"),
  b  = c(1.28, 1.78, 1.34, 1.10, 0.21),
  lo = c(-0.14, -0.11, 0.07, -0.39, -1.04),
  hi = c(2.69, 3.68, 2.62, 2.58, 1.47))
dose$spec <- factor(dose$spec, levels = rev(dose$spec))
ggplot(dose, aes(x = b, y = spec)) +
  geom_vline(xintercept = 0, linetype = "dashed", colour = "grey50") +
  geom_vline(xintercept = 2.5, linetype = "dotted", colour = "#D55E00") +
  geom_pointrange(aes(xmin = lo, xmax = hi), colour = "#0072B2",
                  linewidth = 0.6) +
  labs(x = "Slope of audit reallocation on hearing engagement (pp per SD)",
       y = NULL) +
  theme_bw(base_size = 11)
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-08-24_r27/fig_3.pdf", width = 7, height = 3.5)
