# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: Convention hold rate across 18-22 National Assemblies
library(ggplot2); library(dplyr); library(tidyr)
df <- data.frame(
  na_half = c("18-H1","18-H2","19-H1","19-H2","20-H1","20-H2",
              "21-H1","21-H2","22-H1"),
  held = c(4, 3, 4, 4, 4, 4, 3, 4, 1),
  total = rep(4, 9)
)
df$rate <- df$held / df$total
df$era <- factor(ifelse(df$na_half %in% c("21-H1","21-H2","22-H1"),
                        "Post-supermajority (21-22)",
                        "Pre-supermajority (18-20)"))
ggplot(df, aes(x = na_half, y = rate, group = 1, color = era)) +
  geom_line(color = "grey60", linewidth = 0.6) +
  geom_point(size = 4) +
  scale_color_manual(values = c("Pre-supermajority (18-20)" = "#0072B2",
                                "Post-supermajority (21-22)" = "#D55E00")) +
  scale_y_continuous(limits = c(0, 1.05),
                     breaks = seq(0, 1, 0.25),
                     labels = scales::percent_format(accuracy = 1)) +
  labs(x = "National Assembly (Half)",
       y = "Conventions Held (of 4 applicable)",
       color = NULL,
       title = NULL) +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom",
        panel.grid.minor = element_blank())
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-04-29_r24/fig_1.pdf", width = 7, height = 4.5)
