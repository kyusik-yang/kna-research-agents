#!/usr/bin/env Rscript
# Figure 4: Ruling-Party Passage Advantage by Assembly and Chair Configuration
#
# Computed from KNA parquet data:
#   - master_bills_{17..22}.parquet: bill-level outcomes (passed 0/1)
#   - members_{17..22}.parquet: legislator party metadata
#
# For each member-sponsored bill, classify the chief sponsor's party as
# "ruling" or "opposition" based on who occupied the Blue House at the
# bill's proposal date (ppsl_dt). Compute per-assembly passage rates for
# ruling vs opposition bills, and the difference (ruling - opposition).
#
# Chair configuration is public knowledge about committee chair allocation
# in each assembly, not derivable from the parquet files. Encoded here
# exactly as described in the paper: 17th and 20th are "mixed"; 18th, 19th,
# 21st have chairs dominated by the ruling coalition; 22nd has all chairs
# held by the opposition (unprecedented configuration under Yoon).

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
out_pdf  <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-08_r11/fig_4.pdf"

# ---- Load bills and members -------------------------------------------------
assemblies <- 17:22

read_bills <- function(a) {
  f <- file.path(data_dir, sprintf("master_bills_%d.parquet", a))
  read_parquet(f, col_select = c("bill_id", "age", "ppsr_kind",
                                 "rst_mona_cd", "ppsl_dt", "passed"))
}
read_members <- function(a) {
  f <- file.path(data_dir, sprintf("members_%d.parquet", a))
  read_parquet(f, col_select = c("mona_cd", "age", "party"))
}

bills   <- bind_rows(lapply(assemblies, read_bills))
members <- bind_rows(lapply(assemblies, read_members))

# ---- Party-family classification -------------------------------------------
# Liberal/Democratic-camp party names observed in KNA members files
liberal_parties <- c(
  "열린우리당", "우리당", "민주당", "새천년민주당", "대통합민주신당",
  "통합민주당", "민주통합당", "새정치민주연합", "더불어민주당",
  "더불어시민당", "더불어민주연합", "열린민주당"
)
# Conservative-camp party names
conservative_parties <- c(
  "한나라당", "친박연대", "자유선진당", "국민중심당",
  "새누리당", "미래통합당", "미래한국당", "자유한국당",
  "국민의힘", "국민의미래", "바른미래당"
)

classify_camp <- function(p) {
  ifelse(p %in% liberal_parties, "liberal",
  ifelse(p %in% conservative_parties, "conservative", "other"))
}

members <- members %>% mutate(camp = classify_camp(party))

# ---- Determine ruling camp at each bill's proposal date ---------------------
# Blue House transitions:
#   - Roh (liberal) to 2008-02-25
#   - Lee (conservative) 2008-02-25 to 2013-02-25
#   - Park (conservative) 2013-02-25 to 2017-05-10
#   - Moon (liberal) 2017-05-10 to 2022-05-10
#   - Yoon (conservative) 2022-05-10 onward
ruling_camp_on <- function(d) {
  d <- as.Date(d)
  out <- rep(NA_character_, length(d))
  out[!is.na(d) & d <  as.Date("2008-02-25")] <- "liberal"
  out[!is.na(d) & d >= as.Date("2008-02-25") & d <  as.Date("2017-05-10")] <- "conservative"
  out[!is.na(d) & d >= as.Date("2017-05-10") & d <  as.Date("2022-05-10")] <- "liberal"
  out[!is.na(d) & d >= as.Date("2022-05-10")] <- "conservative"
  out
}

bills <- bills %>%
  mutate(ruling_camp = ruling_camp_on(ppsl_dt))

# ---- Keep only member-sponsored bills with a classifiable sponsor ----------
ml <- bills %>%
  filter(ppsr_kind == "의원", !is.na(rst_mona_cd), !is.na(ruling_camp)) %>%
  left_join(members %>% select(mona_cd, age, camp),
            by = c("rst_mona_cd" = "mona_cd", "age" = "age")) %>%
  filter(camp %in% c("liberal", "conservative")) %>%
  mutate(side = ifelse(camp == ruling_camp, "ruling", "opposition"))

# ---- Per-assembly passage rates --------------------------------------------
rates <- ml %>%
  group_by(age, side) %>%
  summarise(n = n(),
            pass = sum(passed == 1, na.rm = TRUE),
            .groups = "drop") %>%
  mutate(rate = pass / n)

gap_tbl <- rates %>%
  select(age, side, rate) %>%
  pivot_wider(names_from = side, values_from = rate) %>%
  mutate(advantage_pp = 100 * (ruling - opposition))

# ---- Chair configuration (public record, not in parquet) -------------------
chair_cfg <- tibble::tribble(
  ~age, ~chair_config,
  17L, "Mixed",
  18L, "Ruling-aligned",
  19L, "Ruling-aligned",
  20L, "Mixed",
  21L, "Ruling-aligned",
  22L, "All opposition"
)

plot_df <- gap_tbl %>%
  left_join(chair_cfg, by = "age") %>%
  mutate(
    chair_config = factor(chair_config,
                          levels = c("Ruling-aligned", "Mixed", "All opposition")),
    assembly_lbl = paste0(age, "th")
  )

# ---- Plot -------------------------------------------------------------------
okabe <- c("#E69F00","#56B4E9","#009E73","#0072B2","#D55E00","#CC79A7","#000000")
# Ruling-aligned = green, Mixed = grey/yellow, All opposition = red
shape_map <- c("Ruling-aligned" = 16, "Mixed" = 15, "All opposition" = 17)
color_map <- c("Ruling-aligned" = okabe[3],
               "Mixed"          = okabe[1],
               "All opposition" = okabe[5])

p <- ggplot(plot_df, aes(x = factor(age), y = advantage_pp)) +
  geom_hline(yintercept = 0, linetype = "dashed", colour = "grey30") +
  geom_segment(aes(xend = factor(age), y = 0, yend = advantage_pp,
                   colour = chair_config),
               linewidth = 0.6, alpha = 0.6) +
  geom_point(aes(colour = chair_config, shape = chair_config), size = 3.8) +
  geom_text(aes(label = sprintf("%+.1f", advantage_pp)),
            vjust = -1.1, size = 3.1, colour = "grey20") +
  scale_x_discrete(labels = function(x) paste0(x, "th")) +
  scale_y_continuous(
    expand = expansion(mult = c(0.15, 0.25))
  ) +
  scale_colour_manual(values = color_map, name = "Chair configuration") +
  scale_shape_manual(values = shape_map, name = "Chair configuration") +
  labs(
    x = "Assembly",
    y = "Ruling - opposition passage rate (percentage points)"
  ) +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    legend.position = "bottom",
    legend.title = element_text(size = 10),
    legend.text  = element_text(size = 9)
  )

# Use base pdf device to avoid cairo dependency on macOS
ggsave(out_pdf, plot = p, width = 7, height = 4.5, device = "pdf")
