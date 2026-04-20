# fig_4.R - Within-person passage rate changes for women who switched from PR to SMD
# Uses base pdf() device instead of cairo (cairo unavailable on this R install).

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-01_r6/fig_4.pdf"

dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)

okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#000000")

# --- Load members across assemblies 17-22 ----------------------------------
assemblies <- 17:22

members_list <- lapply(assemblies, function(a) {
  f <- file.path(data_dir, paste0("members_", a, ".parquet"))
  df <- as.data.frame(read_parquet(f))
  keep_cols <- intersect(
    c("mona_cd", "member_name", "sex", "age", "election_type", "party"),
    names(df)
  )
  df <- df[, keep_cols, drop = FALSE]
  if (!"age" %in% names(df)) df$age <- a
  df
})
members <- bind_rows(members_list)

# Women only, standardize pathway
women <- members %>%
  filter(sex == "\uc5ec") %>%
  mutate(pathway = case_when(
    election_type == "\ube44\ub840\ub300\ud45c" ~ "PR",
    election_type == "\uc9c0\uc5ed\uad6c"     ~ "SMD",
    TRUE ~ NA_character_
  )) %>%
  filter(!is.na(pathway)) %>%
  select(mona_cd, member_name, age, pathway) %>%
  distinct()

# Identify switchers: PR at least once, then SMD in a later assembly
switcher_ids <- women %>%
  group_by(mona_cd) %>%
  arrange(age, .by_group = TRUE) %>%
  summarise(
    first_pr  = suppressWarnings(min(age[pathway == "PR"],  na.rm = TRUE)),
    last_pr   = suppressWarnings(max(age[pathway == "PR"],  na.rm = TRUE)),
    first_smd = suppressWarnings(min(age[pathway == "SMD"], na.rm = TRUE)),
    .groups = "drop"
  ) %>%
  filter(is.finite(last_pr), is.finite(first_smd), first_smd > last_pr) %>%
  pull(mona_cd)

# --- Load bills and compute per-(member, assembly) passage rates -----------
bill_rates_list <- lapply(assemblies, function(a) {
  f <- file.path(data_dir, paste0("master_bills_", a, ".parquet"))
  df <- as.data.frame(read_parquet(
    f,
    col_select = c("rst_mona_cd", "age", "ppsr_kind", "passed")
  ))
  df %>%
    filter(ppsr_kind == "\uc758\uc6d0",
           !is.na(rst_mona_cd), rst_mona_cd != "",
           !is.na(passed)) %>%
    group_by(mona_cd = rst_mona_cd, age) %>%
    summarise(n_bills = n(),
              passed  = sum(passed, na.rm = TRUE),
              .groups = "drop") %>%
    mutate(passage_rate = passed / n_bills)
})
bill_rates <- bind_rows(bill_rates_list)

# Keep switchers with computable rates
sw <- women %>%
  filter(mona_cd %in% switcher_ids) %>%
  inner_join(bill_rates, by = c("mona_cd", "age")) %>%
  filter(n_bills >= 1)

# For each switcher, take the last PR term and the first SMD term (after PR)
pr_last <- sw %>%
  filter(pathway == "PR") %>%
  group_by(mona_cd, member_name) %>%
  slice_max(age, n = 1, with_ties = FALSE) %>%
  ungroup() %>%
  select(mona_cd, member_name,
         pr_age = age, pr_rate = passage_rate, pr_n = n_bills)

smd_first <- sw %>%
  filter(pathway == "SMD") %>%
  inner_join(pr_last %>% select(mona_cd, pr_age), by = "mona_cd") %>%
  filter(age > pr_age) %>%
  group_by(mona_cd) %>%
  slice_min(age, n = 1, with_ties = FALSE) %>%
  ungroup() %>%
  select(mona_cd,
         smd_age = age, smd_rate = passage_rate, smd_n = n_bills)

pairs_df <- pr_last %>%
  inner_join(smd_first, by = "mona_cd") %>%
  mutate(delta = smd_rate - pr_rate,
         declined = delta < 0)

n_switch   <- nrow(pairs_df)
n_declined <- sum(pairs_df$declined, na.rm = TRUE)
mean_delta <- mean(pairs_df$delta, na.rm = TRUE)

cat("Switchers plotted:", n_switch, "\n")
cat("Declined:", n_declined, "\n")
cat("Mean PR passage rate:",  round(mean(pairs_df$pr_rate),  3), "\n")
cat("Mean SMD passage rate:", round(mean(pairs_df$smd_rate), 3), "\n")
cat("Mean paired diff:",      round(mean_delta, 3), "\n")

# --- Long form for plotting -------------------------------------------------
long_df <- pairs_df %>%
  select(mona_cd, member_name, declined, pr_rate, smd_rate) %>%
  pivot_longer(cols = c(pr_rate, smd_rate),
               names_to = "pathway", values_to = "rate") %>%
  mutate(pathway = factor(ifelse(pathway == "pr_rate", "PR", "SMD"),
                          levels = c("PR", "SMD")))

p <- ggplot(long_df,
            aes(x = pathway, y = rate,
                group = mona_cd, color = declined)) +
  geom_line(alpha = 0.75, linewidth = 0.55) +
  geom_point(size = 1.6, alpha = 0.9) +
  scale_color_manual(
    values = c(`TRUE` = okabe_ito[5], `FALSE` = okabe_ito[4]),
    labels = c(`TRUE` = "Declined", `FALSE` = "Improved or same"),
    name = NULL
  ) +
  scale_y_continuous(labels = scales::percent_format(accuracy = 1),
                     limits = c(0, NA)) +
  labs(x = "Electoral pathway (last PR term vs. first SMD term)",
       y = "Bill passage rate") +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        legend.position = "top",
        legend.key.size = grid::unit(0.8, "lines"))

# --- Save using base pdf() to avoid cairo dependency -----------------------
pdf(out_path, width = 7, height = 4.5, useDingbats = FALSE)
print(p)
invisible(dev.off())

cat("Wrote:", out_path, "\n")
