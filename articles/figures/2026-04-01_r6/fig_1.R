#!/usr/bin/env Rscript
# Figure 1: Bill passage rates by gender and mandate type, 17th-22nd Assemblies.
# All numbers computed from parquet files. PDF saved using base pdf() device
# (cairo_pdf avoided because the local R build has a broken cairo dll).

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
out_pdf  <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-01_r6/fig_1.pdf"
dir.create(dirname(out_pdf), recursive = TRUE, showWarnings = FALSE)

assemblies <- 17:22

# Load bills and members for each assembly, keep only member-sponsored bills,
# join on rst_mona_cd + age to get gender and electoral mandate type.
rows <- lapply(assemblies, function(a) {
  bills_path   <- file.path(data_dir, sprintf("master_bills_%d.parquet", a))
  members_path <- file.path(data_dir, sprintf("members_%d.parquet", a))

  bills <- read_parquet(
    bills_path,
    col_select = c("bill_id", "age", "ppsr_kind", "rst_mona_cd", "passed")
  ) |>
    filter(ppsr_kind == "\uC758\uC6D0",            # member-introduced only
           !is.na(rst_mona_cd),
           rst_mona_cd != "") |>
    mutate(passed = as.integer(passed))

  members <- read_parquet(
    members_path,
    col_select = c("mona_cd", "age", "sex", "election_type")
  ) |>
    filter(!is.na(sex), !is.na(election_type)) |>
    distinct(mona_cd, age, .keep_all = TRUE)

  bills |>
    inner_join(members,
               by = c("rst_mona_cd" = "mona_cd", "age" = "age"))
})

dat <- bind_rows(rows)

# Recode to English labels based on column values (avoid hardcoded Korean in plot).
dat <- dat |>
  mutate(
    gender_en = ifelse(sex == "\uC5EC", "Women", "Men"),
    mandate_en = case_when(
      election_type == "\uBE44\uB840\uB300\uD45C" ~ "PR",
      election_type == "\uC9C0\uC5ED\uAD6C"      ~ "SMD",
      TRUE ~ NA_character_
    )
  ) |>
  filter(!is.na(mandate_en))

# Passage rate by assembly x gender x mandate.
agg <- dat |>
  group_by(age, gender_en, mandate_en) |>
  summarise(
    n_bills = n(),
    n_passed = sum(passed, na.rm = TRUE),
    passage_rate = n_passed / n_bills,
    .groups = "drop"
  ) |>
  mutate(
    group = paste(gender_en, mandate_en),
    group = factor(group, levels = c("Women SMD", "Women PR",
                                     "Men SMD",   "Men PR"))
  )

cat("Aggregated passage rates:\n")
print(agg)

# Okabe-Ito colorblind-safe palette.
pal <- c(
  "Women SMD" = "#D55E00",
  "Women PR"  = "#E69F00",
  "Men SMD"   = "#0072B2",
  "Men PR"    = "#56B4E9"
)
ltys <- c(
  "Women SMD" = "solid",
  "Women PR"  = "dashed",
  "Men SMD"   = "solid",
  "Men PR"    = "dashed"
)
shps <- c(
  "Women SMD" = 16,
  "Women PR"  = 17,
  "Men SMD"   = 15,
  "Men PR"    = 18
)

assembly_lab <- function(x) paste0(x, "th")

p <- ggplot(agg, aes(x = age, y = passage_rate,
                     color = group, linetype = group, shape = group,
                     group = group)) +
  geom_line(linewidth = 0.7) +
  geom_point(size = 2.2) +
  scale_x_continuous(breaks = assemblies, labels = assembly_lab) +
  scale_y_continuous(labels = scales::percent_format(accuracy = 1),
                     limits = c(0, max(agg$passage_rate) * 1.15)) +
  scale_color_manual(values = pal, name = NULL) +
  scale_linetype_manual(values = ltys, name = NULL) +
  scale_shape_manual(values = shps, name = NULL) +
  labs(x = "Assembly", y = "Bill passage rate") +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    legend.position = "bottom",
    legend.key.width = unit(1.2, "lines"),
    legend.margin = margin(t = -4),
    plot.margin = margin(5, 8, 5, 5)
  )

# Save PDF using default pdf device (no cairo) to avoid libSM/libXrender issues.
ggsave(out_pdf, plot = p, width = 7, height = 4.5, device = "pdf",
       useDingbats = FALSE)

cat("Saved:", out_pdf, "\n")
