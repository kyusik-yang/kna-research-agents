# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: Productivity sign reversal across pre/post supermajority
library(ggplot2)
df <- data.frame(
  era = c("Pre-super (18-20)","Pre-super (18-20)",
          "Post-super (21-22)","Post-super (21-22)"),
  chair_party = c("Opposition-chaired","Ruling-chaired",
                  "Opposition-chaired","Ruling-chaired"),
  rate = c(0.367, 0.290, 0.214, 0.304)
)
df$era <- factor(df$era, levels = c("Pre-super (18-20)", "Post-super (21-22)"))
ggplot(df, aes(x = era, y = rate, fill = chair_party)) +
  geom_col(position = position_dodge(width = 0.8), width = 0.7) +
  geom_text(aes(label = scales::percent(rate, accuracy = 0.1)),
            position = position_dodge(width = 0.8),
            vjust = -0.4, size = 3.5) +
  scale_fill_manual(values = c("Opposition-chaired" = "#0072B2",
                                "Ruling-chaired" = "#D55E00")) +
  scale_y_continuous(limits = c(0, 0.45),
                     labels = scales::percent_format(accuracy = 1)) +
  labs(x = NULL, y = "Bill Passage Rate", fill = NULL) +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom",
        panel.grid.minor = element_blank(),
        panel.grid.major.x = element_blank())
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-04-29_r24/fig_2.pdf", width = 7, height = 4.5)
