# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: Passage rates by Gender x Mandate Type x Assembly
library(arrow)
library(dplyr)
library(ggplot2)

members <- arrow::read_parquet(
  "/Users/kyusik/kna/data/processed/member_info_17_22.parquet"
)

bills <- bind_rows(
  arrow::read_parquet("/Users/kyusik/kna/data/processed/master_bills_20.parquet"),
  arrow::read_parquet("/Users/kyusik/kna/data/processed/master_bills_21.parquet"),
  arrow::read_parquet("/Users/kyusik/kna/data/processed/master_bills_22.parquet")
) |>
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
    Group = paste(Gender, Mandate, sep = ", "),
    Assembly = paste0(age, "th")
  ) |>
  group_by(Assembly, Group) |>
  summarise(pass_rate = mean(passed, na.rm = TRUE) * 100, .groups = "drop")

rates$Assembly <- factor(rates$Assembly, levels = c("20th", "21st", "22nd"))
rates$Group <- factor(rates$Group,
  levels = c("Men, PR", "Men, SMD", "Women, PR", "Women, SMD"))

ggplot(rates, aes(x = Assembly, y = pass_rate, fill = Group)) +
  geom_col(position = position_dodge(width = 0.8), width = 0.7) +
  scale_fill_manual(values = c(
    "Men, PR" = "#56B4E9", "Men, SMD" = "#0072B2",
    "Women, PR" = "#E69F00", "Women, SMD" = "#D55E00"
  )) +
  labs(x = NULL, y = "Passage Rate (%)", fill = NULL) +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom")

ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_1.pdf", width = 7, height = 4.5)
