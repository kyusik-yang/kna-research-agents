# Figure 3: Seniority composition by Gender x Mandate, 20th-22nd Assemblies
library(arrow)
library(dplyr)
library(tidyr)
library(ggplot2)

DATA_DIR <- Sys.getenv("KBL_DATA", "/Users/kyusik/kna/data/processed")

members <- read_parquet(file.path(DATA_DIR, "member_info_17_22.parquet")) |>
  filter(assembly %in% 20:22) |>
  mutate(
    Gender = ifelse(gender == "여", "Women", "Men"),
    Mandate = ifelse(election_type == "비례대표", "PR", "SMD"),
    Group = paste(Gender, Mandate, sep = ", "),
    Seniority = ifelse(reelection == "초선", "First-term", "Multi-term"),
    Assembly = paste0(assembly, "th")
  )

comp <- members |>
  count(Assembly, Group, Seniority) |>
  group_by(Assembly, Group) |>
  mutate(pct = n / sum(n) * 100) |>
  ungroup()

comp$Group <- factor(comp$Group,
  levels = c("Women, PR", "Women, SMD", "Men, PR", "Men, SMD"))
comp$Assembly <- factor(comp$Assembly, levels = c("20th", "21st", "22nd"))

ggplot(comp, aes(x = Group, y = pct, fill = Seniority)) +
  geom_col(position = "stack", width = 0.7) +
  facet_wrap(~Assembly) +
  scale_fill_manual(values = c("First-term" = "#CC79A7", "Multi-term" = "#009E73")) +
  labs(x = NULL, y = "Share (%)", fill = NULL) +
  theme_bw(base_size = 11) +
  theme(
    axis.text.x = element_text(angle = 30, hjust = 1, size = 9),
    legend.position = "bottom",
    panel.grid.minor = element_blank()
  )

ggsave("fig_3.pdf", width = 7, height = 4)
cat("Figure 3 done.\n")
