#!/usr/bin/env Rscript

# fig_8.R
# Share of plenary bills that traveled the committee-alternative bypass
# route across the 17th through 22nd National Assemblies.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
})

data_dir <- "/Users/kyusik/kna/data/processed/"
out_path <- "/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_8.pdf"

# Okabe-Ito colorblind-safe palette
okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#000000", "#F0E442")

# Load member info (mona_cd, assembly, gender, election_type, reelection)
members <- read_parquet(file.path(data_dir, "member_info_17_22.parquet")) %>%
  select(mona_cd, assembly, gender, election_type, reelection)

# Load bills for assemblies 17-22 and concatenate
assemblies <- 17:22
bills_list <- lapply(assemblies, function(a) {
  read_parquet(file.path(data_dir, sprintf("master_bills_%d.parquet", a)))
})
bills <- bind_rows(bills_list)

# Restrict to member-sponsored bills
bills <- bills %>% filter(ppsr_kind == "의원")

# Join sponsor attributes from the member table
bills <- bills %>%
  left_join(members, by = c("rst_mona_cd" = "mona_cd", "age" = "assembly"))

# Flag bills that reached the floor through the committee-alternative
# bypass route. In Korean Assembly procedure, the standing committee
# can replace pending member bills with a committee-chair substitute
# ("위원장 대안"); the original member bills are then disposed of with a
# proc_result containing "대안" (e.g., "대안반영폐기"). We treat any
# such disposition as the bypass route.
candidate_cols <- c("proc_result", "proc_result_cd",
                    "rst_proposer_kind", "bill_kind", "bill_name")
present_cols <- intersect(candidate_cols, names(bills))
if (length(present_cols) == 0) {
  stop("No procedural-result column available to detect the bypass route.")
}

bills <- bills %>%
  mutate(
    bypass = Reduce(
      `|`,
      lapply(present_cols, function(col) {
        grepl("대안", as.character(.data[[col]]), fixed = TRUE)
      })
    )
  )

# Aggregate to Assembly-level share
share_by_assembly <- bills %>%
  filter(age %in% assemblies) %>%
  group_by(age) %>%
  summarise(
    n_bills  = n(),
    n_bypass = sum(bypass, na.rm = TRUE),
    share    = n_bypass / n_bills,
    .groups  = "drop"
  ) %>%
  arrange(age)

# Build "17th", "18th", ... x-axis labels
ordinal_suffix <- function(n) {
  ifelse(n %% 100 %in% c(11, 12, 13), "th",
         ifelse(n %% 10 == 1, "st",
                ifelse(n %% 10 == 2, "nd",
                       ifelse(n %% 10 == 3, "rd", "th"))))
}
assembly_levels <- 17:22
assembly_labels <- paste0(assembly_levels, ordinal_suffix(assembly_levels))

p <- ggplot(share_by_assembly, aes(x = age, y = share)) +
  geom_line(color = okabe_ito[4], linewidth = 0.9) +
  geom_point(color = okabe_ito[4], size = 2.6) +
  geom_text(aes(label = sprintf("%.0f%%", 100 * share)),
            vjust = -1.1, size = 3.2) +
  scale_x_continuous(breaks = assembly_levels, labels = assembly_labels) +
  scale_y_continuous(
    labels = function(x) sprintf("%.0f%%", 100 * x),
    limits = c(0.20, 0.60),
    breaks = seq(0.20, 0.60, by = 0.10)
  ) +
  labs(
    x = "National Assembly",
    y = "Share of plenary bills via committee-alternative bypass"
  ) +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank())

ggsave(out_path, plot = p, width = 7, height = 4.5)

# Console diagnostic
cat("Share of committee-alternative bypass bills by Assembly:\n")
print(share_by_assembly)
cat(sprintf("\nFigure saved to: %s\n", out_path))
