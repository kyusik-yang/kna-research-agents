# Paper D, Version 2 (2026-09-26). Figure 3.
# Values are written into this script by the Version 2 rerun of the stored
# Arc 4 analysis samples (OLS with committee fixed effects, SE clustered by
# legislator), with cohort-2 pairs labelled 미래한국당 coded supportive.
# Run from this directory: Rscript fig_3.R
# Within-opposition slopes (pp per within-committee SD) with 95 percent intervals.
library(ggplot2)
dose <- data.frame(
  spec = c("Standardized dose, pooled",
           "Standardized dose, cohort 1",
           "Log dose, pooled",
           "Excl. single-ministry committee",
           "Placebo outcome"),
  b  = c(1.29, 1.78, 1.43, 1.11, 0.36),
  lo = c(-0.15, -0.12, 0.12, -0.40, -0.94),
  hi = c(2.74, 3.68, 2.73, 2.62, 1.66))
dose$spec <- factor(dose$spec, levels = rev(dose$spec))
p <- ggplot(dose, aes(x = b, y = spec)) +
  geom_vline(xintercept = 0, linetype = "dashed", colour = "grey50") +
  geom_vline(xintercept = 2.5, linetype = "dotted", colour = "#D55E00") +
  geom_pointrange(aes(xmin = lo, xmax = hi), colour = "#0072B2", linewidth = 0.6) +
  labs(x = "Slope of audit reallocation on hearing engagement (pp per SD)", y = NULL) +
  theme_bw(base_size = 11)
ggsave("fig_3.pdf", p, width = 7, height = 3.5)
