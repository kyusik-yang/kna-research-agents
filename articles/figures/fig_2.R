# Figure 2: Female x SMD interaction coefficient by assembly (20th-22nd)
library(arrow)
library(dplyr)
library(ggplot2)
library(fixest)

DATA_DIR <- Sys.getenv("KBL_DATA", "/Users/kyusik/kna/data/processed")

members <- read_parquet(file.path(DATA_DIR, "member_info_17_22.parquet"))

results <- list()
for (a in 20:22) {
  bills <- read_parquet(file.path(DATA_DIR, sprintf("master_bills_%d.parquet", a))) |>
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
coef_df$Assembly <- factor(coef_df$Assembly, levels = c("20th", "21st", "22nd"))

ggplot(coef_df, aes(x = estimate, y = Assembly)) +
  geom_pointrange(aes(xmin = ci_low, xmax = ci_high), size = 0.8) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "gray50") +
  labs(
    x = expression(paste("Female ", times, " SMD Interaction (LPM coefficient)")),
    y = NULL,
    caption = "95% CIs. SEs clustered at legislator level."
  ) +
  theme_bw(base_size = 11)

ggsave("fig_2.pdf", width = 7, height = 3.5)
cat("Figure 2 done.\n")
