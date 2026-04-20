# fig_1.R
# Pre-resignation chief-sponsor trajectory by exit channel, 18th-21st Assemblies.
#
# Reproducibility note:
# The paper references a hand-coded clean cohort of 16 members who ran for
# provincial governor or mayor, plus a court-ruling cohort (including the
# UPP December 2014 dissolution). Those hand codings are NOT directly in the
# public KNA parquet. This script computes the closest plausible proxy from
# available fields:
#   - "SMD early exit" (local-executive proxy): single-member-district
#     (지역구) legislators whose last chief-sponsored bill falls inside a
#     window around the 90-day pre-local-election resignation deadline.
#   - "Court-ruling proxy": members in the 19th Assembly whose last bill
#     falls within three months of the UPP dissolution (2014-12-19).
#   - "Continuer pool": legislators whose last bill is within two months
#     of the formal end of the Assembly term (i.e., served the full term).
# Series are labeled in the legend with the proxy rule and observed N, not
# with the paper's hand-coded counts.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
})

data_dir <- Sys.getenv("KBL_DATA",
  unset = "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")

out_pdf <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-18_r18/fig_1.pdf"

# ----- Anchor dates -----------------------------------------------------------

assembly_end <- tibble::tibble(
  age = 18:21,
  term_end = as.Date(c("2012-05-29", "2016-05-29", "2020-05-29", "2024-05-29"))
)

# Korean local elections; public-office candidates must resign ~90 days prior.
local_election <- tibble::tibble(
  age = 18:21,
  election_date = as.Date(c("2010-06-02", "2014-06-04", "2018-06-13", "2022-06-01"))
) %>%
  mutate(resign_deadline = election_date - 90)

upp_dissolution <- as.Date("2014-12-19")

# ----- Load bills (chief-sponsor rows only) -----------------------------------

bill_files <- file.path(data_dir, sprintf("master_bills_%d.parquet", 18:21))

bills <- lapply(bill_files, function(f) {
  read_parquet(f, col_select = c("bill_id", "age", "ppsr_kind",
                                 "rst_mona_cd", "ppsl_dt"))
}) %>%
  bind_rows() %>%
  filter(ppsr_kind == "의원", !is.na(rst_mona_cd)) %>%
  mutate(
    age = as.integer(age),
    ppsl_dt = suppressWarnings(as.Date(substr(as.character(ppsl_dt), 1, 10)))
  ) %>%
  filter(!is.na(ppsl_dt), age %in% 18:21)

# ----- Load members -----------------------------------------------------------

member_files <- file.path(data_dir, sprintf("members_%d.parquet", 18:21))

members <- lapply(member_files, function(f) {
  read_parquet(f, col_select = c("mona_cd", "age", "election_type", "party"))
}) %>%
  bind_rows() %>%
  mutate(age = as.integer(age)) %>%
  filter(age %in% 18:21) %>%
  distinct(mona_cd, age, .keep_all = TRUE)

# ----- Last-bill date per member-assembly -------------------------------------

last_bill <- bills %>%
  group_by(rst_mona_cd, age) %>%
  summarise(last_date = max(ppsl_dt), total_bills = n(), .groups = "drop") %>%
  rename(mona_cd = rst_mona_cd)

member_last <- members %>%
  inner_join(last_bill, by = c("mona_cd", "age")) %>%
  left_join(assembly_end, by = "age") %>%
  left_join(local_election %>% select(age, resign_deadline), by = "age") %>%
  mutate(
    days_to_term_end = as.numeric(term_end - last_date),
    days_to_resign_deadline = as.numeric(last_date - resign_deadline),
    days_to_upp = as.numeric(last_date - upp_dissolution)
  )

# ----- Cohort assignment ------------------------------------------------------

# Local-exec proxy: SMD, last bill inside +/- 120 days of resign deadline,
# AND exit is not a pure end-of-term artifact (last bill at least 60 days
# before formal term end).
# Court-ruling proxy: 19th Assembly, last bill within +/- 90 days of UPP
# dissolution.
# Continuer: last bill within 60 days of formal term end, any type.
member_last <- member_last %>%
  mutate(
    cohort = case_when(
      election_type == "지역구" &
        !is.na(days_to_resign_deadline) &
        abs(days_to_resign_deadline) <= 120 &
        days_to_term_end > 60                    ~ "local_exec",
      age == 19L &
        abs(days_to_upp) <= 90                   ~ "court",
      days_to_term_end <= 60                     ~ "continuer",
      TRUE                                       ~ NA_character_
    )
  ) %>%
  filter(!is.na(cohort)) %>%
  mutate(anchor_date = if_else(cohort == "continuer", term_end, last_date))

cohort_sizes <- member_last %>% count(cohort, name = "n_members")

# ----- Monthly chief-sponsor counts relative to anchor ------------------------

cohort_bills <- bills %>%
  inner_join(
    member_last %>% select(mona_cd, age, cohort, anchor_date),
    by = c("rst_mona_cd" = "mona_cd", "age" = "age")
  ) %>%
  mutate(months_rel = floor(as.numeric(ppsl_dt - anchor_date) / 30.44)) %>%
  filter(months_rel >= -12, months_rel <= 0)

# Sum of chief-sponsored bills for each cohort-month, then per-member mean.
monthly_mean <- cohort_bills %>%
  count(cohort, months_rel, name = "total_bills") %>%
  left_join(cohort_sizes, by = "cohort") %>%
  mutate(mean_bills = total_bills / n_members)

full_grid <- expand_grid(
  cohort = unique(member_last$cohort),
  months_rel = -12:0
) %>%
  left_join(monthly_mean %>% select(cohort, months_rel, mean_bills),
            by = c("cohort", "months_rel")) %>%
  left_join(cohort_sizes, by = "cohort") %>%
  mutate(mean_bills = tidyr::replace_na(mean_bills, 0))

cohort_labels <- c(
  local_exec = "SMD early exit (local-exec proxy)",
  court      = "19th, last bill near UPP dissolution",
  continuer  = "Continuer pool (served to term end)"
)

full_grid <- full_grid %>%
  mutate(cohort_label = sprintf("%s (n = %d)",
                                cohort_labels[cohort], n_members))

# Preserve panel order in the legend.
label_order <- sprintf("%s (n = %d)",
  cohort_labels[c("local_exec", "court", "continuer")],
  cohort_sizes$n_members[match(c("local_exec", "court", "continuer"),
                               cohort_sizes$cohort)])
full_grid$cohort_label <- factor(full_grid$cohort_label, levels = label_order)

# ----- Plot -------------------------------------------------------------------

okabe_ito <- c("#D55E00", "#0072B2", "#009E73")

p <- ggplot(full_grid,
            aes(x = months_rel, y = mean_bills,
                color = cohort_label, shape = cohort_label,
                linetype = cohort_label)) +
  geom_line(linewidth = 0.7) +
  geom_point(size = 2.2) +
  scale_color_manual(values = okabe_ito) +
  scale_shape_manual(values = c(16, 17, 15)) +
  scale_linetype_manual(values = c("solid", "dashed", "dotted")) +
  scale_x_continuous(breaks = seq(-12, 0, 2)) +
  labs(
    x = "Months relative to last chief-sponsored bill (continuers: months relative to term end)",
    y = "Mean chief-sponsor bills per member-month",
    color = NULL, shape = NULL, linetype = NULL
  ) +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "bottom",
    legend.direction = "vertical",
    legend.box = "vertical",
    legend.margin = margin(0, 0, 0, 0),
    legend.key.width = unit(1.2, "cm"),
    panel.grid.minor = element_blank()
  ) +
  guides(color = guide_legend(ncol = 1))

ggsave(out_pdf, p, width = 7, height = 4.5)
