# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: Committee-level passage rate changes around December 3
library(ggplot2)
library(dplyr)

committees <- data.frame(
  committee = c("Culture/Sports/Tourism",
                "Industry/SME",
                "Agriculture/Fisheries",
                "Health/Welfare",
                "Education",
                "Judiciary (all bills)",
                "Defense/Foreign Affairs",
                "Strategy/Finance"),
  change = c(-41.0, -28.1, -27.1, -26.2, -25.6, -18.2, -8.3, 28.0),
  type = c("Social policy", "Economic", "Social policy",
            "Social policy", "Social policy", "Judiciary",
            "Security", "Economic")
)

# Okabe-Ito palette subset
palette <- c("Social policy" = "#E69F00", "Economic" = "#56B4E9",
             "Judiciary" = "#009E73", "Security" = "#D55E00")

ggplot(committees, aes(x = change,
                       y = reorder(committee, change),
                       color = type)) +
  geom_point(size = 3) +
  geom_segment(aes(xend = 0, yend = committee), linewidth = 0.6) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "gray50") +
  scale_color_manual(values = palette, name = "Committee type") +
  labs(x = "Change in passage rate (percentage points)",
       y = NULL,
       caption = paste("Note: Change = post-Dec. 3 rate minus",
                       "pre-Dec. 3 rate. Selected committees shown.")) +
  theme_bw(base_size = 11) +
  theme(legend.position = c(0.82, 0.25),
        legend.background = element_rect(fill = "white", color = "gray80"),
        plot.caption = element_text(hjust = 0, size = 8))
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_1.pdf", width = 7, height = 4.5)
