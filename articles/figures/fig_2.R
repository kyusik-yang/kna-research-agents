# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: Special counsel bill escalation across assemblies
library(ggplot2)

sc_data <- data.frame(
  assembly = factor(c("17th", "18th", "19th", "20th", "21st", "22nd"),
                    levels = c("17th", "18th", "19th", "20th", "21st", "22nd")),
  introduced = c(19, 12, 14, 37, 34, 70),
  passed = c(3, 2, 3, 2, 6, 17),
  rejected = c(0, 0, 0, 0, 3, 8)
)

library(tidyr)
sc_long <- sc_data %>%
  pivot_longer(cols = c(passed, rejected),
               names_to = "outcome", values_to = "count")

ggplot() +
  geom_col(data = sc_data, aes(x = assembly, y = introduced),
           fill = "gray85", width = 0.6) +
  geom_col(data = sc_long, aes(x = assembly, y = count, fill = outcome),
           position = "dodge", width = 0.5) +
  scale_fill_manual(values = c("passed" = "#009E73", "rejected" = "#D55E00"),
                    labels = c("Passed", "Rejected"),
                    name = "Outcome") +
  labs(x = "National Assembly", y = "Number of bills",
       caption = paste("Note: Gray bars = total special counsel bills introduced.",
                       "Colored bars = final outcomes.")) +
  theme_bw(base_size = 11) +
  theme(legend.position = c(0.15, 0.85),
        legend.background = element_rect(fill = "white", color = "gray80"),
        plot.caption = element_text(hjust = 0, size = 8))
ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_2.pdf", width = 7, height = 4.5)
