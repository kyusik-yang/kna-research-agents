# Paper D, Version 2 (2026-09-26). Figure 2.
# Values are written into this script by the Version 2 rerun of the stored
# Arc 4 analysis samples (OLS with committee fixed effects, SE clustered by
# legislator), with cohort-2 pairs labelled 미래한국당 coded supportive.
# Run from this directory: Rscript fig_2.R
# Estimates with 90 percent intervals against margins of 5 and 2.5 points.
library(ggplot2)
eq <- data.frame(
  test = c("Main DiD", "Placebo DiD"),
  b  = c(-0.72, -1.09),
  lo = c(-2.60, -2.61),
  hi = c(1.15, 0.43))
eq$test <- factor(eq$test, levels = rev(eq$test))
p <- ggplot(eq, aes(x = b, y = test)) +
  geom_vline(xintercept = c(-5, 5), linetype = "dashed", colour = "#D55E00") +
  geom_vline(xintercept = c(-2.5, 2.5), linetype = "dotted", colour = "#009E73") +
  geom_vline(xintercept = 0, colour = "grey60") +
  geom_pointrange(aes(xmin = lo, xmax = hi), colour = "#0072B2", linewidth = 0.7) +
  labs(x = "Change in ministry share of audit questions (pp, 90% CI)", y = NULL) +
  theme_bw(base_size = 11)
ggsave("fig_2.pdf", p, width = 7, height = 3)
