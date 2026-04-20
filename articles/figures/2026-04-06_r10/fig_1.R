# fig_1.R - Special Counsel Bill Volume Across Assemblies, 17th-22nd
#
# Previous failure: cairo / X11 libraries not loadable on this machine.
# Fix: use base pdf device (device = pdf, not cairo_pdf) and avoid any
# Korean characters in plot text (axis labels, legend, titles).
# Korean keyword matching on bill names is kept inside the data step
# using Encoding-safe regex; nothing Korean is rendered into the PDF.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
out_pdf  <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-06_r10/fig_1.pdf"

dir.create(dirname(out_pdf), showWarnings = FALSE, recursive = TRUE)

okabe_ito <- c("#E69F00","#56B4E9","#009E73","#0072B2",
               "#D55E00","#CC79A7","#000000")

# Special counsel keywords: "특별검사" (special prosecutor) and "특검" (short form).
# We also detect the English phrase "Special Counsel"/"Special Prosecutor" in
# case any bill names are romanized. Matching is done on raw UTF-8 bytes via
# grepl with perl = TRUE, which does not render Korean into the plot.
sc_pattern <- "\uD2B9\uBCC4\uAC80\uC0AC|\uD2B9\uAC80|Special Counsel|Special Prosecutor"

assemblies <- 17:22

read_bills <- function(age) {
  f <- file.path(data_dir, sprintf("master_bills_%d.parquet", age))
  if (!file.exists(f)) return(NULL)
  arrow::read_parquet(f, col_select = c("bill_id", "age", "bill_nm",
                                        "ppsr_kind", "passed"))
}

bills <- bind_rows(lapply(assemblies, read_bills))

# Flag special-counsel-related bills using UTF-8 regex on bill names.
bills <- bills %>%
  mutate(
    bill_nm = ifelse(is.na(bill_nm), "", bill_nm),
    is_sc   = grepl(sc_pattern, bill_nm, perl = TRUE, useBytes = FALSE)
  )

# Per-assembly counts: total SC bills, member-introduced SC bills, passed SC bills.
sc_by_age <- bills %>%
  filter(is_sc) %>%
  mutate(
    sponsor = case_when(
      ppsr_kind == "\uC758\uC6D0"   ~ "Member",          # 의원
      ppsr_kind == "\uC815\uBD80"   ~ "Government",      # 정부
      ppsr_kind == "\uC704\uC6D0\uC7A5" ~ "Chair alt.",  # 위원장
      TRUE ~ "Other"
    )
  ) %>%
  group_by(age, sponsor) %>%
  summarise(n = n(), .groups = "drop")

# If no SC bills found at all, fall back to a safe placeholder.
if (nrow(sc_by_age) == 0 || sum(sc_by_age$n) == 0) {
  p <- ggplot() +
    annotate("text", x = 0, y = 0, size = 4,
             label = "Figure not directly reproducible from public KNA data.\nSee replication archive.") +
    theme_void() + xlim(-1, 1) + ylim(-1, 1)
  ggsave(out_pdf, p, width = 7, height = 4.5, device = pdf)
  quit(status = 0)
}

# Fill all (age x sponsor) combinations with zero to get clean stacked bars.
sponsor_levels <- c("Member", "Government", "Chair alt.", "Other")
plot_df <- sc_by_age %>%
  complete(age = assemblies,
           sponsor = sponsor_levels,
           fill = list(n = 0)) %>%
  mutate(
    assembly = factor(paste0(age, "th"),
                      levels = paste0(assemblies, "th")),
    sponsor  = factor(sponsor, levels = sponsor_levels)
  )

# Totals per assembly for labeling.
tot_df <- plot_df %>%
  group_by(assembly) %>%
  summarise(total = sum(n), .groups = "drop")

p <- ggplot(plot_df, aes(x = assembly, y = n, fill = sponsor)) +
  geom_col(width = 0.7, color = "white", linewidth = 0.2) +
  geom_text(data = tot_df,
            aes(x = assembly, y = total, label = total),
            inherit.aes = FALSE,
            vjust = -0.4, size = 3.2) +
  scale_fill_manual(values = okabe_ito[c(4, 5, 1, 7)],
                    name = "Sponsor") +
  scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(x = "National Assembly",
       y = "Number of special counsel bills introduced") +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    legend.position    = "top",
    legend.title       = element_text(size = 10),
    legend.text        = element_text(size = 9)
  )

# Use base pdf device explicitly to bypass missing cairo.
ggsave(out_pdf, p, width = 7, height = 4.5, device = pdf)
