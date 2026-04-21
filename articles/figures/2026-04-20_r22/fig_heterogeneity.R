#!/usr/bin/env Rscript
# fig_3.R
# Distribution of individual-member pre-exit sponsorship deltas
# for a 16-member cohort, grouped by exit cycle (2010 / 2018 / 2022).

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
})

# Okabe-Ito colorblind-safe palette
okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#F0E442", "#000000")

data_dir  <- "/Users/kyusik/kna/data/processed/"
out_path  <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-20_r22/fig_heterogeneity.pdf"

# --- Load members ---------------------------------------------------------
members <- read_parquet(file.path(data_dir, "member_info_17_22.parquet"))

# --- Load bills (17-22) ---------------------------------------------------
bill_files <- file.path(data_dir, sprintf("master_bills_%d.parquet", 17:22))
bill_files <- bill_files[file.exists(bill_files)]
bills <- bind_rows(lapply(bill_files, read_parquet))

# --- Filter member-sponsored bills and join to members -------------------
member_bills <- bills %>%
  filter(ppsr_kind == "의원") %>%
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "age" = "assembly"))

# Count sponsorships per member per assembly
member_counts <- member_bills %>%
  group_by(mona_cd = rst_mona_cd, assembly = age) %>%
  summarise(n_bills = n(), .groups = "drop")

# --- Identify exit term (last assembly served) ---------------------------
member_assemblies <- members %>%
  distinct(mona_cd, assembly) %>%
  group_by(mona_cd) %>%
  summarise(last_assembly = max(assembly),
            n_terms       = n_distinct(assembly),
            .groups = "drop")

final_counts <- member_counts %>%
  inner_join(member_assemblies, by = "mona_cd") %>%
  filter(assembly == last_assembly) %>%
  select(mona_cd, last_assembly, n_final = n_bills)

prior_counts <- member_counts %>%
  inner_join(member_assemblies, by = "mona_cd") %>%
  filter(assembly == last_assembly - 1L) %>%
  select(mona_cd, n_prior = n_bills)

deltas <- member_assemblies %>%
  filter(n_terms >= 2) %>%
  inner_join(final_counts, by = c("mona_cd", "last_assembly")) %>%
  inner_join(prior_counts, by = "mona_cd") %>%
  mutate(delta = n_final - n_prior)

# --- Map last-served assembly to exit-cycle label ------------------------
# 18th assembly (2008-2012) -> "2010" subcohort
# 20th assembly (2016-2020) -> "2018" subcohort
# 21st assembly (2020-2024) -> "2022" subcohort
exit_map <- c("18" = "2010", "20" = "2018", "21" = "2022")
deltas <- deltas %>%
  mutate(exit_cycle = exit_map[as.character(last_assembly)]) %>%
  filter(!is.na(exit_cycle))

# --- Build the 16-member cohort (cycle-stratified) -----------------------
set.seed(20260420)
per_cycle <- c("2010" = 5L, "2018" = 5L, "2022" = 6L)

cohort <- deltas %>%
  group_by(exit_cycle) %>%
  group_modify(~ {
    n_pick <- min(per_cycle[[unique(.y$exit_cycle)]], nrow(.x))
    slice_sample(.x, n = n_pick)
  }) %>%
  ungroup()

# Anonymize with cycle-preserving identifiers, ordered by delta
cohort <- cohort %>%
  arrange(exit_cycle, delta) %>%
  group_by(exit_cycle) %>%
  mutate(member_id = sprintf("%s-M%02d", exit_cycle, row_number())) %>%
  ungroup()

cohort$member_id <- factor(cohort$member_id,
                           levels = cohort$member_id[order(cohort$delta)])

pooled_mean <- mean(cohort$delta)

# --- Plot ----------------------------------------------------------------
p <- ggplot(cohort,
            aes(x = delta, y = member_id,
                color = exit_cycle, shape = exit_cycle)) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "grey30") +
  geom_vline(xintercept = pooled_mean, linetype = "dotted", color = "black") +
  geom_point(size = 2.8) +
  scale_color_manual(values = c("2010" = okabe_ito[1],
                                "2018" = okabe_ito[2],
                                "2022" = okabe_ito[5]),
                     name = "Exit cycle") +
  scale_shape_manual(values = c("2010" = 16, "2018" = 17, "2022" = 15),
                     name = "Exit cycle") +
  labs(x = "Pre-exit sponsorship delta (final term minus prior term)",
       y = "Cohort member (anonymized)") +
  theme_bw(base_size = 11) +
  theme(panel.grid.major.y = element_blank(),
        panel.grid.minor   = element_blank(),
        legend.position    = "right")

ggsave(out_path, plot = p, width = 7, height = 4.5)
