# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: Career coefficient plot before and after committee FE
library(ggplot2); library(dplyr)

coef_data <- data.frame(
  career = rep(c("Prosecutor", "Lawyer", "Academic",
                 "Journalist", "Military", "Activist"), 2),
  estimate = c(0.183, 0.130, -0.020, -0.043, -0.028, -0.004,
               0.006, 0.008, 0.003, -0.004, -0.009, 0.001),
  se = c(0.003, 0.006, 0.005, 0.004, 0.005, 0.004,
         0.003, 0.005, 0.004, 0.004, 0.004, 0.004),
  model = rep(c("Without Committee FE", "With Committee FE"), each = 6)
)
coef_data$lower <- coef_data$estimate - 1.96 * coef_data$se
coef_data$upper <- coef_data$estimate + 1.96 * coef_data$se
coef_data$model <- factor(coef_data$model,
  levels = c("Without Committee FE", "With Committee FE"))
coef_data$career <- factor(coef_data$career,
  levels = c("Prosecutor","Lawyer","Academic",
             "Journalist","Military","Activist"))

oi_colors <- c("#E69F00","#56B4E9","#009E73",
               "#F0E442","#0072B2","#D55E00")

ggplot(coef_data, aes(x = career, y = estimate, color = career)) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "grey50") +
  geom_pointrange(aes(ymin = lower, ymax = upper), size = 0.6) +
  facet_wrap(~model, scales = "free_y") +
  scale_color_manual(values = oi_colors) +
  theme_bw(base_size = 11) +
  theme(axis.text.x = element_text(angle = 35, hjust = 1),
        legend.position = "none",
        strip.background = element_blank()) +
  labs(x = NULL,
       y = "Coefficient on Legal Keyword Indicator",
       title = NULL)
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/fig_1.pdf", width = 7, height = 4.5)
