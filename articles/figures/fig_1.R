# Figure 1: Passage rates by Gender x Mandate Type, 17th-22nd Assemblies
library(arrow)
library(dplyr)
library(ggplot2)

DATA_DIR <- Sys.getenv("KBL_DATA", "/Users/kyusik/kna/data/processed")

members <- read_parquet(file.path(DATA_DIR, "member_info_17_22.parquet"))

bills <- bind_rows(lapply(17:22, function(a) {
  f <- file.path(DATA_DIR, sprintf("master_bills_%d.parquet", a))
  if (file.exists(f)) read_parquet(f) else NULL
})) |>
  filter(ppsr_kind == "의원")

merged <- bills |>
  left_join(
    members |> select(mona_cd, assembly, gender, election_type),
    by = c("rst_mona_cd" = "mona_cd", "age" = "assembly")
  ) |>
  filter(!is.na(gender), !is.na(election_type))

rates <- merged |>
  mutate(
    Gender = ifelse(gender == "여", "Women", "Men"),
    Mandate = ifelse(election_type == "비례대표", "PR", "SMD"),
    Group = paste(Gender, Mandate, sep = ", ")
  ) |>
  group_by(age, Group) |>
  summarise(
    pass_rate = mean(passed, na.rm = TRUE) * 100,
    n_bills = n(),
    .groups = "drop"
  )

rates$Group <- factor(rates$Group,
  levels = c("Women, SMD", "Women, PR", "Men, SMD", "Men, PR"))

okabe <- c(
  "Women, SMD" = "#D55E00",
  "Women, PR"  = "#E69F00",
  "Men, SMD"   = "#0072B2",
  "Men, PR"    = "#56B4E9"
)

ggplot(rates, aes(x = age, y = pass_rate, color = Group, group = Group)) +
  geom_line(linewidth = 0.9) +
  geom_point(size = 2.5) +
  scale_color_manual(values = okabe) +
  scale_x_continuous(breaks = 17:22, labels = paste0(17:22, "th")) +
  labs(x = "Assembly", y = "Passage Rate (%)", color = NULL) +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "bottom",
    legend.key.width = unit(1.5, "cm"),
    panel.grid.minor = element_blank()
  )

ggsave("fig_1.pdf", width = 7, height = 4.5)
cat("Figure 1 done. Rows:", nrow(rates), "\n")
