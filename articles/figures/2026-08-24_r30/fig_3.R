# fig_3.R - Raw strict passage rates by lead-sponsor seniority (17th-22nd Assemblies pooled)
# Point-range plot with 95% binomial confidence intervals

library(arrow)
library(dplyr)
library(ggplot2)

data_dir <- "/Users/kyusik/kna/data/processed"
out_path <- "/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/2026-08-24_r30/fig_3.pdf"

# ---- Load members ----
members <- read_parquet(file.path(data_dir, "member_info_17_22.parquet")) %>%
  select(mona_cd, assembly, reelection) %>%
  mutate(assembly = as.integer(assembly))

# ---- Load bills (member-sponsored only), pooled over 17th-22nd Assemblies ----
bills <- bind_rows(lapply(17:22, function(a) {
  read_parquet(file.path(data_dir, sprintf("master_bills_%d.parquet", a))) %>%
    filter(ppsr_kind == "의원") %>%   # 의원 = member bill
    select(rst_mona_cd, age, passed) %>%
    mutate(age = as.integer(age))
}))

# ---- Join lead sponsor info (sponsor id + matching assembly) ----
merged <- bills %>%
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "age" = "assembly")) %>%
  filter(!is.na(reelection), !is.na(passed))

# ---- Four seniority categories ----
merged <- merged %>%
  mutate(
    seniority = case_when(
      reelection == "초선" ~ "First term",    # 초선
      reelection == "재선" ~ "Second term",   # 재선
      reelection == "3선"      ~ "Third term",    # 3선
      TRUE                          ~ "Fourth+ term"  # 4선 이상
    ),
    seniority = factor(
      seniority,
      levels = c("First term", "Second term", "Third term", "Fourth+ term")
    )
  )

# ---- Raw strict passage rates with exact 95% binomial CIs ----
summ <- merged %>%
  group_by(seniority) %>%
  summarise(
    n = n(),
    k = sum(passed == 1),
    .groups = "drop"
  ) %>%
  rowwise() %>%
  mutate(
    rate = k / n,
    ci_lo = binom.test(k, n)$conf.int[1],
    ci_hi = binom.test(k, n)$conf.int[2]
  ) %>%
  ungroup()

# ---- Okabe-Ito colorblind palette ----
okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2")

# ---- Plot ----
p <- ggplot(summ, aes(x = seniority, y = rate, color = seniority)) +
  geom_pointrange(aes(ymin = ci_lo, ymax = ci_hi), linewidth = 0.8, size = 0.6) +
  scale_color_manual(values = okabe_ito, guide = "none") +
  scale_y_continuous(labels = function(x) sprintf("%.1f%%", 100 * x)) +
  labs(
    x = "Lead sponsor seniority",
    y = "Strict passage rate",
    title = "Strict passage rates by lead-sponsor seniority",
    subtitle = "Member bills, 17th-22nd Assemblies pooled; 95% binomial CIs"
  ) +
  theme_bw(base_size = 11)

dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
ggsave(out_path, plot = p, width = 7, height = 4.5)
