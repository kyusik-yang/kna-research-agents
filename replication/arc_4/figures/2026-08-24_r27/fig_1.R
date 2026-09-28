# Paper D, Version 2 (2026-09-26). Figure 1.
# Values are written into this script by the Version 2 rerun of the stored
# Arc 4 analysis samples (OLS with committee fixed effects, SE clustered by
# legislator), with cohort-2 pairs labelled 미래한국당 coded supportive.
# Run from this directory: Rscript fig_1.R
# Estimates in percentage points with 95 percent intervals.
library(ggplot2)
est <- data.frame(
  spec = c("Pooled, cohorts 1 and 2",
           "Cohort 1 (2020-21)",
           "Cohort 2 (2023)",
           "Cohort 3 (2022, govt change)",
           "Keyword coding (diagnostic)",
           "Placebo agencies"),
  b  = c(-0.72, -1.07, 1.09, 0.09, -1.56, -1.09),
  lo = c(-2.96, -3.57, -3.39, -3.80, -4.81, -2.90),
  hi = c(1.51, 1.44, 5.56, 3.99, 1.70, 0.72))
est$spec <- factor(est$spec, levels = rev(est$spec))
p <- ggplot(est, aes(x = b, y = spec)) +
  geom_vline(xintercept = 0, linetype = "dashed", colour = "grey50") +
  geom_vline(xintercept = c(-5, 5), linetype = "dotted", colour = "#D55E00") +
  geom_pointrange(aes(xmin = lo, xmax = hi), colour = "#0072B2", linewidth = 0.6) +
  labs(x = "Change in confirmed-ministry share of audit questions (pp)", y = NULL) +
  theme_bw(base_size = 11)
ggsave("fig_1.pdf", p, width = 7, height = 4.5)
