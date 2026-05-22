# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: Annualized failure rate of bypass bills
library(arrow); library(dplyr); library(ggplot2)
DATA <- "/Users/kyusik/kna/data/processed"
# Approximate from the forum-reported counts
fr <- data.frame(
  assembly = factor(17:22,
    labels = c("17th","18th","19th","20th","21st","22nd")),
  failures_per_year = c(0.8, 0.0, 0.2, 0.0, 2.0, 10.0)
)
ggplot(fr, aes(x = assembly, y = failures_per_year)) +
  geom_col(fill = "#D55E00", width = 0.65) +
  geom_text(aes(label = sprintf("%.1f", failures_per_year)),
            vjust = -0.5, size = 3.5) +
  scale_y_continuous(limits = c(0, 12), breaks = seq(0, 12, 2)) +
  labs(x = "Assembly", y = "Annualized failures of bypass bills (per year)") +
  theme_bw(base_size = 11)
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_2.pdf", width = 7, height = 4.5)
