# fig_1.R
# Grouped bar chart: member bills introduced per Assembly (17th-22nd),
# split by first-term vs. re-elected lead sponsors.

library(arrow)
library(dplyr)
library(ggplot2)

data_dir <- "/Users/kyusik/kna/data/processed"
fig_path <- "/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-08-24_r30/fig_1.pdf"

# Okabe-Ito colorblind-safe palette (first two hues)
okabe_ito <- c("First-term" = "#E69F00", "Re-elected" = "#56B4E9")

# Member info for the 17th-22nd Assemblies
members <- read_parquet(file.path(data_dir, "member_info_17_22.parquet")) %>%
  select(mona_cd, assembly, reelection)

# Load member-sponsored bills for each Assembly and join lead sponsor info
bills <- bind_rows(lapply(17:22, function(a) {
  read_parquet(file.path(data_dir, sprintf("master_bills_%d.parquet", a))) %>%
    filter(ppsr_kind == "의원") %>%
    select(rst_mona_cd, age)
}))

plot_df <- bills %>%
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "age" = "assembly")) %>%
  filter(!is.na(reelection)) %>%
  mutate(
    sponsor_type = ifelse(reelection == "초선", "First-term", "Re-elected"),
    assembly = factor(age, levels = 17:22, labels = paste0(17:22, "th"))
  ) %>%
  count(assembly, sponsor_type, name = "n_bills")

p <- ggplot(plot_df, aes(x = assembly, y = n_bills, fill = sponsor_type)) +
  geom_col(position = position_dodge(width = 0.8), width = 0.7) +
  scale_fill_manual(values = okabe_ito, name = "Lead sponsor") +
  scale_y_continuous(labels = scales::comma, expand = expansion(mult = c(0, 0.05))) +
  labs(
    x = "Assembly",
    y = "Member bills introduced"
  ) +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "bottom",
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank()
  )

ggsave(fig_path, plot = p, width = 7, height = 4.5)
