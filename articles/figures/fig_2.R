# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: Coefficient plot of Female x SMD interaction by assembly
library(arrow)
library(dplyr)
library(ggplot2)
library(fixest)

members <- arrow::read_parquet(
  "/Users/kyusik/kna/data/processed/member_info_17_22.parquet"
)

results <- list()
for (a in c(20, 21, 22)) {
  bills <- arrow::read_parquet(
    sprintf("/Users/kyusik/kna/data/processed/master_bills_%d.parquet", a)
  ) |>
    filter(ppsr_kind == "의원")

  merged <- bills |>
    left_join(
      members |> filter(assembly == a) |> select(mona_cd, gender, election_type),
      by = c("rst_mona_cd" = "mona_cd")
    ) |>
    filter(!is.na(gender), !is.na(election_type)) |>
    mutate(
      female = as.integer(gender == "여"),
      smd = as.integer(election_type == "지역구")
    )

  model <- feols(passed ~ female * smd, data = merged, vcov = ~rst_mona_cd)
  ci <- confint(model)

  results[[length(results) + 1]] <- data.frame(
    Assembly = paste0(a, "th"),
    estimate = coef(model)["female:smd"],
    ci_low = ci["female:smd", 1],
    ci_high = ci["female:smd", 2]
  )
}

coef_df <- bind_rows(results)
coef_df$Assembly <- factor(coef_df$Assembly, levels = c("22nd", "21st", "20th"))

ggplot(coef_df, aes(x = estimate, y = Assembly)) +
  geom_pointrange(aes(xmin = ci_low, xmax = ci_high), size = 0.8) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "gray50") +
  labs(
    x = "Female x SMD Interaction (LPM coefficient)",
    y = NULL,
    caption = "Note: 95% CIs. SEs clustered at legislator level."
  ) +
  theme_bw(base_size = 11)

ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_2.pdf", width = 7, height = 3.5)
