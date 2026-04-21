# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: Per-cycle sensitivity band of pre-resignation sponsorship delta
library(ggplot2); library(dplyr)
cycles <- data.frame(
  cycle = factor(c("2010", "2014", "2018", "2022", "Pooled"),
                 levels = c("2010", "2014", "2018", "2022", "Pooled")),
  N = c(4, 3, 5, 4, 16),
  election_anchor = c(-1.40, -1.85, -1.55, -1.20, -1.50),
  lastvote_anchor = c(-1.09, -1.06, -0.91, -0.05, -0.77)
)
cycles_long <- tidyr::pivot_longer(cycles,
  cols = c(election_anchor, lastvote_anchor),
  names_to = "spec", values_to = "delta")
cycles_long$spec <- factor(cycles_long$spec,
  levels = c("election_anchor", "lastvote_anchor"),
  labels = c("Election anchored (R19)", "Last-vote anchored (R22)"))
okabe <- c("Election anchored (R19)" = "#0072B2",
           "Last-vote anchored (R22)" = "#D55E00")
ggplot(cycles_long, aes(x = delta, y = cycle, color = spec, shape = spec)) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "grey40") +
  geom_point(size = 3.2) +
  scale_color_manual(values = okabe) +
  scale_shape_manual(values = c(16, 17)) +
  labs(x = "Pre-Exit Sponsorship Delta (bills/month)",
       y = "Exit Cycle", color = "Specification", shape = "Specification") +
  theme_bw(base_size = 11) + theme(legend.position = "bottom")
ggsave("/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-20_r22/fig_sensitivity.pdf", width = 7, height = 4.2)
