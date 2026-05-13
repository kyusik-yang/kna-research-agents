#!/usr/bin/env Rscript
# fig_8.R
# Two-line plot: women's share of seats and PR share among women legislators
# across 17th-22nd National Assemblies.

library(arrow)
library(dplyr)
library(ggplot2)
library(tidyr)

data_dir <- "/Users/kyusik/kna/data/processed/"
out_path <- "/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_8.pdf"

# Okabe-Ito colorblind-safe palette
okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#000000", "#F0E442")

# Load member info
members <- read_parquet(file.path(data_dir, "member_info_17_22.parquet"))

# Compute, per assembly:
#   1) women's share of seats
#   2) share of women elected via proportional representation (비례대표)
seat_summary <- members %>%
  filter(!is.na(assembly), !is.na(gender)) %>%
  group_by(assembly) %>%
  summarise(
    n_total = n(),
    n_women = sum(gender == "여", na.rm = TRUE),
    women_share = 100 * n_women / n_total,
    .groups = "drop"
  )

pr_among_women <- members %>%
  filter(!is.na(assembly), gender == "여", !is.na(election_type)) %>%
  group_by(assembly) %>%
  summarise(
    n_women = n(),
    n_pr = sum(election_type == "비례대표", na.rm = TRUE),
    pr_share = 100 * n_pr / n_women,
    .groups = "drop"
  )

plot_df <- seat_summary %>%
  select(assembly, women_share) %>%
  left_join(pr_among_women %>% select(assembly, pr_share), by = "assembly") %>%
  filter(assembly %in% 17:22) %>%
  pivot_longer(
    cols = c(women_share, pr_share),
    names_to = "series",
    values_to = "value"
  ) %>%
  mutate(
    series = factor(
      series,
      levels = c("women_share", "pr_share"),
      labels = c("Women's share of seats",
                 "PR share among women legislators")
    )
  )

# Build x-axis labels like "17th", "18th", ...
ordinal_suffix <- function(n) {
  ifelse(n %% 100 %in% c(11, 12, 13), "th",
         ifelse(n %% 10 == 1, "st",
                ifelse(n %% 10 == 2, "nd",
                       ifelse(n %% 10 == 3, "rd", "th"))))
}
assembly_levels <- 17:22
assembly_labels <- paste0(assembly_levels, ordinal_suffix(assembly_levels))

p <- ggplot(plot_df, aes(x = assembly, y = value,
                         color = series, shape = series, linetype = series)) +
  geom_line(linewidth = 0.8) +
  geom_point(size = 2.5) +
  geom_text(aes(label = sprintf("%.1f", value)),
            vjust = -1.0, size = 3, show.legend = FALSE) +
  scale_x_continuous(breaks = assembly_levels, labels = assembly_labels) +
  scale_y_continuous(limits = c(0, 100),
                     breaks = seq(0, 100, by = 20),
                     labels = function(x) paste0(x, "%")) +
  scale_color_manual(values = c(okabe_ito[4], okabe_ito[5])) +
  scale_shape_manual(values = c(16, 17)) +
  scale_linetype_manual(values = c("solid", "dashed")) +
  labs(
    x = "National Assembly",
    y = "Percent",
    color = NULL, shape = NULL, linetype = NULL
  ) +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "bottom",
    legend.key.width = unit(1.5, "lines"),
    panel.grid.minor = element_blank()
  )

ggsave(out_path, plot = p, width = 7, height = 4.5)
