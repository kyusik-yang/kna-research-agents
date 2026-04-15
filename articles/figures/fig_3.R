# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 3: Committee-switcher convergence slopegraph
library(ggplot2); library(dplyr); library(tidyr)

switch_data <- data.frame(
  legislator = c("Jeong S.H.", "Jeong J.S.", "Kim J.M.",
                 "Baek H.R.", "Jo E.C.", "Kwon S.D.",
                 "Jang J.W.", "Yun H.H.", "Kwon C.S."),
  old_comm = c("Judiciary","Judiciary","Judiciary",
               "Judiciary","Judiciary","Judiciary",
               "Judiciary","Industry","Industry"),
  new_comm = c("Defense","Agriculture","Pol. Affairs",
               "Pol. Affairs","Land/Transport","Agriculture",
               "Science/ICT","Judiciary","Judiciary"),
  old_rate = c(52.0, 45.1, 42.1, 39.1, 30.9, 28.2, 27.8, 2.2, 6.2),
  new_rate = c(16.7, 11.3, 12.6, 7.6, 4.7, 6.1, 1.9, 35.6, 24.1),
  new_baseline = c(5.6, 6.5, 9.5, 9.5, 5.7, 6.5, 6.8, 32.3, 32.3)
)
switch_long <- switch_data |>
  select(legislator, old_rate, new_rate) |>
  pivot_longer(cols = c(old_rate, new_rate),
               names_to = "period", values_to = "legal_pct") |>
  mutate(period = ifelse(period == "old_rate",
    "20th Assembly\n(Pre-Switch)", "21st Assembly\n(Post-Switch)"),
    period = factor(period, levels = c(
      "20th Assembly\n(Pre-Switch)", "21st Assembly\n(Post-Switch)")),
    direction = ifelse(legislator %in% c("Yun H.H.","Kwon C.S."),
                       "To Judiciary", "From Judiciary"))

oi_cols <- c("From Judiciary" = "#D55E00", "To Judiciary" = "#0072B2")

ggplot(switch_long,
       aes(x = period, y = legal_pct, group = legislator,
           color = direction)) +
  geom_line(linewidth = 0.8, alpha = 0.7) +
  geom_point(size = 2.5) +
  geom_text(data = switch_long |> filter(
    period == "21st Assembly\n(Post-Switch)"),
    aes(label = legislator), hjust = -0.12, size = 2.8) +
  scale_color_manual(values = oi_cols, name = "Switch Direction") +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom") +
  labs(x = NULL,
       y = "Legal Keyword Rate (%)",
       title = NULL) +
  scale_y_continuous(limits = c(0, 56), breaks = seq(0, 55, 10))
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/fig_3.pdf", width = 7, height = 4.5)
