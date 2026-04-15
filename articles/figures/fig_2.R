# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: Committee-level legal keyword density
library(ggplot2); library(dplyr)

comm_data <- data.frame(
  committee = c("Judiciary", "Political Affairs",
                "Science/ICT", "Agriculture",
                "Land/Transport", "Defense"),
  legal_pct = c(32.3, 9.5, 6.8, 6.5, 5.7, 5.6)
)
comm_data$committee <- factor(comm_data$committee,
  levels = comm_data$committee[order(comm_data$legal_pct)])

oi_fill <- c("#0072B2","#56B4E9","#009E73",
             "#E69F00","#D55E00","#CC79A7")

ggplot(comm_data, aes(x = committee, y = legal_pct, fill = committee)) +
  geom_col(width = 0.7) +
  geom_hline(yintercept = 8.1, linetype = "dashed",
             color = "grey40", linewidth = 0.5) +
  annotate("text", x = 1.5, y = 9.5,
           label = "Non-judiciary average (8.1%)",
           size = 3, color = "grey30") +
  scale_fill_manual(values = oi_fill) +
  coord_flip() +
  theme_bw(base_size = 11) +
  theme(legend.position = "none") +
  labs(x = NULL,
       y = "Legal Keyword Rate (%)",
       title = NULL) +
  scale_y_continuous(limits = c(0, 36),
                     breaks = seq(0, 35, 5))
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/fig_2.pdf", width = 7, height = 4.5)
