# fig_2.R (Paper E, version 2, 2026-09-26)
# Strict passage rates of member law bills by Assembly and by the lead sponsor's
# seniority at that Assembly, with exact 95% binomial confidence intervals.
#
# Strict passage: proc_rslt is 원안가결 or 수정가결. Version 1 of this figure
# plotted the `passed` column, which also counts 대안반영폐기 (bills absorbed
# into a committee alternative), under a "strict passage" label, and it split
# sponsors by the lifetime seniority count. Both are corrected here.
# Sample and seniority rule as in fig_1.R.
#
# Data: the KNA processed files at commit 3d8d55d of github.com/kyusik-yang/kna
# (main branch). Later revisions of those files change the sample, and the
# stopifnot() check below then fails on purpose.
# Run from this directory with KBL_DATA set to the KNA processed-data folder:
#   Rscript fig_2.R

library(arrow)
library(dplyr)
library(ggplot2)

data_dir <- Sys.getenv("KBL_DATA")
if (data_dir == "") stop("Set KBL_DATA to the KNA processed-data directory")

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
    select(rst_mona_cd, proc_rslt) %>%
    mutate(assembly = a)
}))

rates <- bills %>%
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "assembly" = "assembly")) %>%
  mutate(
    strict = as.integer(proc_rslt %in% c("원안가결", "수정가결")),
    sponsor_type = ifelse(term_number == 1, "First term", "Re-elected")
  ) %>%
  group_by(assembly, sponsor_type) %>%
  summarise(n = n(), k = sum(strict), .groups = "drop") %>%
  rowwise() %>%
  mutate(rate = k / n,
         ci_lo = binom.test(k, n)$conf.int[1],
         ci_hi = binom.test(k, n)$conf.int[2]) %>%
  ungroup()

stopifnot(sum(rates$n) == 93572)

okabe_ito <- c("First term" = "#E69F00", "Re-elected" = "#0072B2")
dodge <- position_dodge(width = 0.3)

p <- ggplot(rates, aes(x = assembly, y = rate, color = sponsor_type, group = sponsor_type)) +
  geom_line(linewidth = 0.6, position = dodge) +
  geom_pointrange(aes(ymin = ci_lo, ymax = ci_hi), size = 0.35, position = dodge) +
  scale_color_manual(values = okabe_ito, name = "Lead sponsor, seniority at the Assembly") +
  scale_x_continuous(breaks = 17:22, labels = c("17th", "18th", "19th", "20th", "21st", "22nd")) +
  scale_y_continuous(labels = scales::percent_format(accuracy = 1), limits = c(0, NA)) +
  labs(x = "Assembly", y = "Strict passage rate") +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom", panel.grid.minor = element_blank())

ggsave("fig_2.pdf", plot = p, width = 7, height = 4.5)
