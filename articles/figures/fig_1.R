# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: Legislative funnel by sponsor bloc, 22nd Assembly
library(arrow); library(dplyr); library(ggplot2); library(tidyr)
DATA <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
bills <- read_parquet(file.path(DATA, "master_bills_22.parquet"))
members <- read_parquet(file.path(DATA, "members_22.parquet"))
bills_leg <- bills |> filter(ppsr_kind == "의원")
bills_leg <- bills_leg |>
  left_join(members |> select(mona_cd, party), by = c("rst_mona_cd" = "mona_cd"))
ruling <- c("국민의힘", "국민의미래")
bills_leg <- bills_leg |>
  mutate(bloc = ifelse(party %in% ruling, "Ruling", "Opposition"))
funnel <- bills_leg |>
  filter(!is.na(bloc)) |>
  group_by(bloc) |>
  summarise(
    N = n(),
    `Committee assigned` = mean(!is.na(committee_nm), na.rm = TRUE),
    `Presented` = mean(!is.na(cmt_present_dt), na.rm = TRUE),
    `Committee processed` = mean(!is.na(cmt_proc_dt), na.rm = TRUE),
    `Plenary processed` = mean(!is.na(proc_dt), na.rm = TRUE),
    Passed = mean(passed == 1, na.rm = TRUE)
  ) |>
  pivot_longer(-c(bloc, N), names_to = "stage", values_to = "rate")
funnel$stage <- factor(funnel$stage, levels = c(
  "Committee assigned", "Presented", "Committee processed",
  "Plenary processed", "Passed"))
pal <- c("Ruling" = "#E69F00", "Opposition" = "#0072B2")
ggplot(funnel, aes(x = stage, y = rate, fill = bloc)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.6) +
  scale_fill_manual(values = pal, name = "Sponsor Bloc") +
  scale_y_continuous(labels = scales::percent_format(), limits = c(0, 1)) +
  labs(x = NULL, y = "Share of Bills", title = NULL) +
  theme_bw(base_size = 11) +
  theme(axis.text.x = element_text(angle = 25, hjust = 1),
        legend.position = "top")
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/fig_1.pdf", width = 7, height = 4.5)
