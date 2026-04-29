# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 3: Cycle-21 judiciary placebo - bill volume and passage rate
library(ggplot2); library(dplyr); library(tidyr)
df <- data.frame(
  cell = c("21-H1\n(Broken)", "21-H2\n(Restored)", "22-H1\n(Broken)"),
  bills = c(1280, 729, 1519),
  passage_rate = c(0.194, 0.147, 0.166)
)
df$cell <- factor(df$cell, levels = c("21-H1\n(Broken)",
                                       "21-H2\n(Restored)",
                                       "22-H1\n(Broken)"))
df_long <- df |>
  tidyr::pivot_longer(cols = c(bills, passage_rate),
                      names_to = "metric", values_to = "value") |>
  mutate(metric_label = ifelse(metric == "bills",
                               "Bills Sponsored",
                               "Passage Rate"))
ggplot(df_long, aes(x = cell, y = value, fill = metric_label)) +
  geom_col(show.legend = FALSE) +
  facet_wrap(~ metric_label, scales = "free_y") +
  scale_fill_manual(values = c("Bills Sponsored" = "#0072B2",
                                "Passage Rate" = "#D55E00")) +
  labs(x = "Legislation and Judiciary Committee (NA-Half, Convention Status)",
       y = NULL) +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        panel.grid.major.x = element_blank(),
        strip.background = element_rect(fill = "grey95"))
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-04-29_r24/fig_3.pdf", width = 7, height = 4.5)
