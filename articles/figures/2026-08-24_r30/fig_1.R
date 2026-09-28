# fig_1.R (Paper E, version 2, 2026-09-26)
# Member law bills introduced per Assembly (17th-22nd), by the lead sponsor's
# seniority at that Assembly (first term vs. re-elected).
#
# Sample: bills with ppsr_kind == "의원" and bill_kind == "법률안" and a lead
# sponsor code, joined to that Assembly's member file on mona_cd (the R28 panel
# definition, 93,572 bills).
# Seniority at the Assembly: the member files' `reelection` field is the
# lifetime count at collection, so the term number at Assembly a is
# (lifetime count) - (terms served in the 17th-22nd) + (rank of a among them).
# Version 1 of this figure used the lifetime count directly.
#
# Data: the KNA processed files at commit 3d8d55d of github.com/kyusik-yang/kna
# (main branch). Later revisions of those files change the sample, and the
# stopifnot() check below then fails on purpose.
# Run from this directory with KBL_DATA set to the KNA processed-data folder:
#   Rscript fig_1.R

library(arrow)
library(dplyr)
library(ggplot2)

data_dir <- Sys.getenv("KNA_DATA_V060")  # published figure: pinned to the kna v0.6.0 data
if (!dir.exists(data_dir)) stop("KNA_DATA_V060 must name the data/processed folder of kna v0.6.0. ",
                             "Run scripts/setup_kna_v060.sh (see KNA_070_PUBLISHED.md).")
fig_path <- "articles/figures/2026-08-24_r30/fig_1.pdf"

lifetime_count <- function(x) {
  ifelse(x == "초선", 1L, ifelse(x == "재선", 2L, suppressWarnings(as.integer(sub("선$", "", x)))))
}

members <- bind_rows(lapply(17:22, function(a) {
  read_parquet(file.path(data_dir, sprintf("members_%d.parquet", a))) %>%
    select(mona_cd, reelection) %>%
    mutate(assembly = a)
})) %>%
  mutate(lifetime = lifetime_count(reelection)) %>%
  group_by(mona_cd) %>%
  arrange(assembly, .by_group = TRUE) %>%
  mutate(term_number = lifetime - n() + row_number()) %>%
  ungroup()

bills <- bind_rows(lapply(17:22, function(a) {
  read_parquet(file.path(data_dir, sprintf("master_bills_%d.parquet", a))) %>%
    filter(ppsr_kind == "의원", bill_kind == "법률안", !is.na(rst_mona_cd)) %>%
    select(rst_mona_cd) %>%
    mutate(assembly = a)
}))

plot_df <- bills %>%
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "assembly" = "assembly")) %>%
  mutate(
    sponsor_type = ifelse(term_number == 1, "First term", "Re-elected"),
    assembly = factor(assembly, levels = 17:22,
                      labels = c("17th", "18th", "19th", "20th", "21st", "22nd"))
  ) %>%
  count(assembly, sponsor_type, name = "n_bills")

stopifnot(sum(plot_df$n_bills) == 93572)

okabe_ito <- c("First term" = "#E69F00", "Re-elected" = "#56B4E9")

p <- ggplot(plot_df, aes(x = assembly, y = n_bills, fill = sponsor_type)) +
  geom_col(position = position_dodge(width = 0.8), width = 0.7) +
  scale_fill_manual(values = okabe_ito, name = "Lead sponsor, seniority at the Assembly") +
  scale_y_continuous(labels = scales::comma, expand = expansion(mult = c(0, 0.05))) +
  labs(x = "Assembly", y = "Member law bills introduced") +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "bottom",
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank()
  )

ggsave("fig_1.pdf", plot = p, width = 7, height = 4.5)
