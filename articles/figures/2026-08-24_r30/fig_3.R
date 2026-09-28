# fig_3.R (Paper E, version 2, 2026-09-26)
# Strict passage rates by the lead sponsor's seniority at the Assembly, member
# law bills of the 17th-22nd Assemblies pooled, with exact 95% binomial
# confidence intervals.
#
# Strict passage: proc_rslt is 원안가결 or 수정가결. Version 1 of this figure
# plotted the `passed` column (which also counts 대안반영폐기) and grouped
# sponsors by the lifetime seniority count. Both are corrected here.
# Sample and seniority rule as in fig_1.R.
#
# Data: the KNA processed files at commit 3d8d55d of github.com/kyusik-yang/kna
# (main branch). Later revisions of those files change the sample, and the
# stopifnot() check below then fails on purpose.
# Run from this directory with KBL_DATA set to the KNA processed-data folder:
#   Rscript fig_3.R

library(arrow)
library(dplyr)
library(ggplot2)

data_dir <- Sys.getenv("KNA_DATA_V060")  # published figure: pinned to the kna v0.6.0 data
if (!dir.exists(data_dir)) stop("KNA_DATA_V060 must name the data/processed folder of kna v0.6.0. ",
                             "Run scripts/setup_kna_v060.sh (see KNA_070_PUBLISHED.md).")
out_path <- "articles/figures/2026-08-24_r30/fig_3.pdf"

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

summ <- bills %>%
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "assembly" = "assembly")) %>%
  mutate(
    strict = as.integer(proc_rslt %in% c("원안가결", "수정가결")),
    seniority = factor(pmin(term_number, 4L), levels = 1:4,
                       labels = c("First term", "Second term", "Third term", "Fourth term or more"))
  ) %>%
  group_by(seniority) %>%
  summarise(n = n(), k = sum(strict), .groups = "drop") %>%
  rowwise() %>%
  mutate(rate = k / n,
         ci_lo = binom.test(k, n)$conf.int[1],
         ci_hi = binom.test(k, n)$conf.int[2]) %>%
  ungroup()

stopifnot(sum(summ$n) == 93572)
print(summ)

okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2")

p <- ggplot(summ, aes(x = seniority, y = rate, color = seniority)) +
  geom_pointrange(aes(ymin = ci_lo, ymax = ci_hi), linewidth = 0.8, size = 0.6) +
  scale_color_manual(values = okabe_ito, guide = "none") +
  scale_y_continuous(labels = function(x) sprintf("%.1f%%", 100 * x)) +
  labs(x = "Lead sponsor seniority at the Assembly", y = "Strict passage rate") +
  theme_bw(base_size = 11)

ggsave("fig_3.pdf", plot = p, width = 7, height = 4.5)
