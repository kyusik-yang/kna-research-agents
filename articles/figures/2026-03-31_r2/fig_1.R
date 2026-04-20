# fig_1.R
# DPK Dissent Trajectory on Comprehensive Real Estate Tax Votes, 21st Assembly
# Data: roll_calls_all.parquet + master_bills_21.parquet
# All numbers computed at runtime - no hardcoded percentages.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- Sys.getenv("KBL_DATA",
                      "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")

# Five comprehensive real estate tax (종합부동산세) floor votes, 21st Assembly,
# identified by bill_no from the paper's roll-call table.
target_bill_nos <- c("2101804", "2105946", "2112216", "2116313", "2120968")
vote_date_label <- c("2101804" = "Jul 2020",
                     "2105946" = "Dec 2020",
                     "2112216" = "Aug 2021",
                     "2116313" = "Jul 2022",
                     "2120968" = "Mar 2023")

# Load 21st Assembly bill master, keep only the five target bills.
bills <- read_parquet(file.path(data_dir, "master_bills_21.parquet")) %>%
  filter(bill_no %in% target_bill_nos) %>%
  select(bill_id, bill_no) %>%
  distinct()

# Load individual roll-call records for those bill_ids.
roll <- read_parquet(file.path(data_dir, "roll_calls_all.parquet")) %>%
  filter(bill_id %in% bills$bill_id) %>%
  left_join(bills, by = "bill_id")

# Define DPK (Democratic Party of Korea) membership liberally to cover
# any label variants stored in the roll-call file.
dpk_pattern <- "더불어민주당|민주당"

# Dissent rate: among DPK legislators who cast a substantive vote
# (찬성 / 반대 / 기권), the share who did NOT vote with the party majority.
# On each of these bills the DPK majority voted 찬성 (yes), so dissent =
# (반대 + 기권) / (찬성 + 반대 + 기권). 불참 (absent) is excluded from the
# denominator because absence is not observable dissent.
dpk_stats <- roll %>%
  filter(grepl(dpk_pattern, party)) %>%
  filter(vote %in% c("찬성", "반대", "기권")) %>%
  group_by(bill_no) %>%
  summarise(
    n_present = n(),
    n_yes     = sum(vote == "찬성"),
    n_no      = sum(vote == "반대"),
    n_abstain = sum(vote == "기권"),
    .groups = "drop"
  ) %>%
  mutate(
    dissent_pct = 100 * (n_no + n_abstain) / n_present,
    label       = factor(vote_date_label[bill_no],
                         levels = unname(vote_date_label)),
    era         = ifelse(bill_no %in% c("2101804", "2105946", "2112216"),
                         "Moon government (DPK in power)",
                         "Yoon government (PPP in power)")
  ) %>%
  arrange(label)

# Okabe-Ito palette.
okabe <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
           "#D55E00", "#CC79A7", "#000000")

# x-axis positions for drawing the government-transition separator
# between the Aug 2021 vote (position 3) and the Jul 2022 vote (position 4).
transition_x <- 3.5

p <- ggplot(dpk_stats,
            aes(x = label, y = dissent_pct, group = 1)) +
  annotate("rect",
           xmin = transition_x, xmax = Inf,
           ymin = -Inf, ymax = Inf,
           fill = "grey92", alpha = 0.6) +
  annotate("text",
           x = transition_x, y = max(dpk_stats$dissent_pct) * 1.08,
           label = "May 2022: government\ntransition (DPK -> PPP)",
           hjust = 0.5, vjust = 0, size = 2.9, lineheight = 0.95,
           colour = "grey30") +
  geom_line(colour = okabe[4], linewidth = 0.7) +
  geom_point(aes(colour = era, shape = era), size = 3.2) +
  geom_text(aes(label = sprintf("%.1f%%", dissent_pct)),
            vjust = -1.1, size = 3.2, colour = "grey20") +
  scale_colour_manual(values = c(
    "Moon government (DPK in power)" = okabe[4],
    "Yoon government (PPP in power)" = okabe[5]
  )) +
  scale_shape_manual(values = c(
    "Moon government (DPK in power)" = 16,
    "Yoon government (PPP in power)" = 17
  )) +
  scale_y_continuous(
    limits = c(0, max(dpk_stats$dissent_pct) * 1.25),
    expand = expansion(mult = c(0, 0.02))
  ) +
  labs(
    x = NULL,
    y = "DPK dissent rate (%)",
    colour = NULL,
    shape  = NULL
  ) +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    legend.position = "bottom",
    legend.margin = margin(t = -4),
    plot.margin = margin(6, 10, 4, 6)
  )

out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-03-31_r2/fig_1.pdf"
dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)
ggsave(out_path, p, width = 7, height = 4.5)
