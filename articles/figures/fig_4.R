# Figure 4: Within-person passage rate changes for PR-to-SMD switchers
library(arrow)
library(dplyr)
library(tidyr)
library(ggplot2)

DATA_DIR <- Sys.getenv("KBL_DATA", "/Users/kyusik/kna/data/processed")

members <- read_parquet(file.path(DATA_DIR, "member_info_17_22.parquet"))

# Load all bills
bills <- bind_rows(lapply(17:22, function(a) {
  f <- file.path(DATA_DIR, sprintf("master_bills_%d.parquet", a))
  if (file.exists(f)) read_parquet(f) else NULL
})) |>
  filter(ppsr_kind == "의원")

# Compute legislator-assembly passage rates
leg_rates <- bills |>
  left_join(
    members |> select(mona_cd, assembly, gender, election_type, name_kr),
    by = c("rst_mona_cd" = "mona_cd", "age" = "assembly")
  ) |>
  filter(!is.na(gender), gender == "여") |>
  group_by(rst_mona_cd, name_kr, age, election_type) |>
  summarise(
    pass_rate = mean(passed, na.rm = TRUE) * 100,
    n_bills = n(),
    .groups = "drop"
  )

# Find women who switched from PR to SMD across consecutive assemblies
switchers <- leg_rates |>
  arrange(rst_mona_cd, age) |>
  group_by(rst_mona_cd) |>
  filter(n() >= 2) |>
  mutate(
    prev_type = lag(election_type),
    prev_rate = lag(pass_rate),
    prev_age = lag(age)
  ) |>
  filter(election_type == "지역구" & prev_type == "비례대표") |>
  ungroup()

if (nrow(switchers) == 0) {
  # Fallback: any women who served in both PR and SMD (not necessarily consecutive)
  pr_terms <- leg_rates |> filter(election_type == "비례대표")
  smd_terms <- leg_rates |> filter(election_type == "지역구")
  both <- inner_join(
    pr_terms |> group_by(rst_mona_cd, name_kr) |>
      summarise(pr_rate = weighted.mean(pass_rate, n_bills), pr_age = max(age), .groups = "drop"),
    smd_terms |> group_by(rst_mona_cd, name_kr) |>
      summarise(smd_rate = weighted.mean(pass_rate, n_bills), smd_age = min(age), .groups = "drop"),
    by = c("rst_mona_cd", "name_kr")
  ) |>
    filter(smd_age > pr_age)

  plot_data <- both |>
    mutate(
      id = row_number(),
      declined = smd_rate < pr_rate
    ) |>
    pivot_longer(cols = c(pr_rate, smd_rate), names_to = "phase", values_to = "rate") |>
    mutate(phase = ifelse(phase == "pr_rate", "Last PR Term", "First SMD Term"))
} else {
  plot_data <- switchers |>
    mutate(
      id = row_number(),
      declined = pass_rate < prev_rate
    ) |>
    select(id, name_kr, declined,
           pr_rate = prev_rate, smd_rate = pass_rate) |>
    pivot_longer(cols = c(pr_rate, smd_rate), names_to = "phase", values_to = "rate") |>
    mutate(phase = ifelse(phase == "pr_rate", "Last PR Term", "First SMD Term"))
}

plot_data$phase <- factor(plot_data$phase, levels = c("Last PR Term", "First SMD Term"))

n_total <- length(unique(plot_data$id))
n_declined <- plot_data |>
  filter(phase == "Last PR Term") |>
  summarise(n = sum(declined)) |>
  pull(n)

ggplot(plot_data, aes(x = phase, y = rate, group = id)) +
  geom_line(aes(color = declined), alpha = 0.6, linewidth = 0.7) +
  geom_point(aes(color = declined), size = 2) +
  scale_color_manual(
    values = c("TRUE" = "#D55E00", "FALSE" = "#009E73"),
    labels = c("TRUE" = "Declined", "FALSE" = "Improved"),
    name = NULL
  ) +
  geom_hline(yintercept = 0, linetype = "dotted", color = "gray70") +
  labs(
    x = NULL,
    y = "Passage Rate (%)",
    caption = sprintf("%d of %d switchers experienced lower passage rates after transitioning.",
                      n_declined, n_total)
  ) +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom")

ggsave("fig_4.pdf", width = 7, height = 4.5)
cat("Figure 4 done. Switchers:", n_total, "Declined:", n_declined, "\n")
