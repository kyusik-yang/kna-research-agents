#!/usr/bin/env Rscript

# fig_9.R
# Two-line plot of mean bills sponsored per legislator across the 17th to 22nd
# Assemblies, comparing women and men.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
})

# Okabe-Ito colorblind palette
okabe_ito <- c(
  "#E69F00", "#56B4E9", "#009E73", "#0072B2",
  "#D55E00", "#CC79A7", "#000000"
)

data_dir <- "/Users/kyusik/kna/data/processed"
out_path <- "/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_9.pdf"

# Load member info
members <- read_parquet(file.path(data_dir, "member_info_17_22.parquet")) %>%
  select(mona_cd, assembly, gender, election_type, reelection)

# Load and combine bills for assemblies 17 through 22
assemblies <- 17:22

bills_list <- lapply(assemblies, function(a) {
  f <- file.path(data_dir, sprintf("master_bills_%d.parquet", a))
  read_parquet(f) %>%
    filter(ppsr_kind == "의원") %>%
    select(rst_mona_cd, age, ppsr_kind)
})

bills <- bind_rows(bills_list)

# Join bills to members: rst_mona_cd = mona_cd AND age = assembly
joined <- bills %>%
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "age" = "assembly"))

# Count bills per legislator-assembly-gender
bills_per_leg <- joined %>%
  group_by(age, gender, rst_mona_cd) %>%
  summarise(n_bills = n(), .groups = "drop")

# Ensure legislators with zero bills are included: build the full panel from members
panel <- members %>%
  filter(assembly %in% assemblies, !is.na(gender)) %>%
  left_join(
    bills_per_leg,
    by = c("mona_cd" = "rst_mona_cd", "assembly" = "age", "gender" = "gender")
  ) %>%
  mutate(n_bills = ifelse(is.na(n_bills), 0, n_bills))

# Mean bills per legislator by assembly and gender
agg <- panel %>%
  group_by(assembly, gender) %>%
  summarise(mean_bills = mean(n_bills), .groups = "drop") %>%
  mutate(
    gender_label = ifelse(gender == "여", "Women", "Men")
  )

# Plot
p <- ggplot(agg, aes(x = assembly, y = mean_bills,
                     color = gender_label, shape = gender_label,
                     group = gender_label)) +
  geom_line(linewidth = 0.8) +
  geom_point(size = 2.5) +
  scale_color_manual(values = c("Women" = okabe_ito[1], "Men" = okabe_ito[4])) +
  scale_shape_manual(values = c("Women" = 16, "Men" = 17)) +
  scale_x_continuous(breaks = assemblies,
                     labels = paste0(assemblies, "th")) +
  labs(
    x = "National Assembly",
    y = "Mean bills sponsored per legislator",
    color = NULL,
    shape = NULL
  ) +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "top",
    panel.grid.minor = element_blank()
  )

ggsave(out_path, plot = p, width = 7, height = 4.5)
