# fig_2.R - Raw strict passage rates of member bills, first-term vs re-elected
# lead sponsors, 17th-22nd Assemblies

library(arrow)
library(dplyr)
library(ggplot2)

data_dir <- "/Users/kyusik/kna/data/processed"
out_path <- "/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-08-24_r30/fig_2.pdf"

# --- Load data --------------------------------------------------------------

members <- read_parquet(file.path(data_dir, "member_info_17_22.parquet")) %>%
  mutate(assembly = as.integer(assembly)) %>%
  select(mona_cd, assembly, reelection)

bills <- bind_rows(lapply(17:22, function(a) {
  read_parquet(file.path(data_dir, sprintf("master_bills_%d.parquet", a))) %>%
    select(age, rst_mona_cd, ppsr_kind, passed) %>%
    mutate(age = as.integer(age))
}))

# --- Member bills joined to lead-sponsor info -------------------------------

member_bills <- bills %>%
  filter(ppsr_kind == "의원") %>%
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "age" = "assembly")) %>%
  filter(!is.na(reelection)) %>%
  mutate(
    sponsor_group = if_else(reelection == "초선", "First-term", "Re-elected")
  )

# --- Raw strict passage rates by Assembly and sponsor group -----------------

pass_rates <- member_bills %>%
  group_by(age, sponsor_group) %>%
  summarise(
    n_bills   = n(),
    pass_rate = mean(as.numeric(passed), na.rm = TRUE),
    .groups   = "drop"
  )

# --- Plot -------------------------------------------------------------------

# Okabe-Ito colorblind-safe palette
okabe_ito <- c("First-term" = "#E69F00", "Re-elected" = "#0072B2")

p <- ggplot(pass_rates,
            aes(x = age, y = pass_rate,
                color = sponsor_group, group = sponsor_group)) +
  geom_line(linewidth = 0.8) +
  geom_point(size = 2.2) +
  scale_color_manual(values = okabe_ito, name = "Lead sponsor") +
  scale_x_continuous(breaks = 17:22, labels = paste0(17:22, "th")) +
  scale_y_continuous(labels = scales::percent_format(accuracy = 1)) +
  labs(
    x = "Assembly",
    y = "Strict passage rate",
    title = "Strict Passage Rates of Member Bills by Lead Sponsor Seniority",
    subtitle = "First-term vs. re-elected lead sponsors, 17th-22nd Assemblies"
  ) +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "bottom",
    panel.grid.minor = element_blank()
  )

dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
ggsave(out_path, plot = p, width = 7, height = 4.5)
