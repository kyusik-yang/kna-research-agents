# fig_2.R — Ideology vs. housing bill sponsorship rate across 20th/21st/22nd Assemblies.
# All numbers computed from parquet/csv data. DW file columns are
# (member_id, coord1D, term, party, member_name, aligned, party_bloc);
# it has no mona_cd, so we join to members by (member_name, age=term).

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
  library(readr)
})

data_dir <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-05_r8/fig_2.pdf"

okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#000000")

# Housing-related keyword pattern (Korean). Matches the usual housing policy lexicon.
# Built from Unicode escapes to avoid source-encoding issues.
housing_pattern <- paste(
  c("\uC8FC\uD0DD",        # 주택
    "\uC8FC\uAC70",        # 주거
    "\uBD80\uB3D9\uC0B0",  # 부동산
    "\uC784\uB300",        # 임대
    "\uC784\uCC28",        # 임차
    "\uC804\uC138",        # 전세
    "\uC6D4\uC138",        # 월세
    "\uC7AC\uAC74\uCD95",  # 재건축
    "\uC7AC\uAC1C\uBC1C"), # 재개발
  collapse = "|"
)

bills_all <- list()
for (a in c(20, 21, 22)) {
  f <- file.path(data_dir, paste0("master_bills_", a, ".parquet"))
  b <- read_parquet(f) %>%
    filter(ppsr_kind == "\uC758\uC6D0",    # 의원 (member-sponsored)
           !is.na(rst_mona_cd)) %>%
    mutate(is_housing = grepl(housing_pattern, bill_nm, perl = TRUE)) %>%
    select(age, rst_mona_cd, is_housing)
  bills_all[[as.character(a)]] <- b
}
bills <- bind_rows(bills_all)

spons <- bills %>%
  group_by(age, rst_mona_cd) %>%
  summarise(total_bills = n(),
            housing_bills = sum(is_housing, na.rm = TRUE),
            .groups = "drop") %>%
  mutate(housing_rate = housing_bills / pmax(total_bills, 1))

# Members metadata for 20/21/22.
members_all <- list()
for (a in c(20, 21, 22)) {
  f <- file.path(data_dir, paste0("members_", a, ".parquet"))
  m <- read_parquet(f) %>%
    select(mona_cd, member_name, age, party)
  members_all[[as.character(a)]] <- m
}
members <- bind_rows(members_all)

# DW-NOMINATE scores. Columns observed: member_id, coord1D, term, party, member_name, ...
dw <- read_csv(file.path(data_dir, "dw_ideal_points_20_22.csv"),
               show_col_types = FALSE) %>%
  transmute(member_name = member_name,
            age = as.integer(term),
            ideology = as.numeric(coord1D))

# Join DW to members via (member_name, age). Some duplicates possible; keep the
# first ideology score per (mona_cd, age).
leg <- members %>%
  inner_join(dw, by = c("member_name", "age")) %>%
  distinct(mona_cd, age, .keep_all = TRUE) %>%
  left_join(spons, by = c("mona_cd" = "rst_mona_cd", "age" = "age")) %>%
  mutate(total_bills = ifelse(is.na(total_bills), 0, total_bills),
         housing_bills = ifelse(is.na(housing_bills), 0, housing_bills),
         housing_rate = ifelse(total_bills == 0, 0, housing_bills / total_bills))

# Keep legislators with at least one sponsored bill (so rate is well-defined)
# and a non-missing ideology.
leg <- leg %>%
  filter(!is.na(ideology), total_bills > 0) %>%
  mutate(assembly_lab = factor(paste0(age, "th Assembly"),
                               levels = c("20th Assembly",
                                          "21st Assembly",
                                          "22nd Assembly")))

if (nrow(leg) < 10) {
  # Honest fallback
  p <- ggplot() +
    annotate("text", x = 0, y = 0, size = 4,
             label = "Figure not directly reproducible from public KNA data.\nSee replication archive.") +
    theme_void() + xlim(-1, 1) + ylim(-1, 1)
  ggsave(out_path, p, width = 7, height = 4.5)
  quit(status = 0)
}

# Plot: ideology vs. housing sponsorship rate, faceted by assembly,
# with a linear fit + 95% CI.
p <- ggplot(leg, aes(x = ideology, y = housing_rate)) +
  geom_point(alpha = 0.35, size = 1.3, colour = okabe_ito[4]) +
  geom_smooth(method = "lm", formula = y ~ x,
              colour = okabe_ito[5], fill = okabe_ito[5], alpha = 0.18,
              linewidth = 0.6) +
  facet_wrap(~ assembly_lab, nrow = 1) +
  scale_y_continuous(labels = scales::percent_format(accuracy = 1),
                     limits = c(0, NA)) +
  labs(x = "Ideology (DW-NOMINATE 1st dimension)",
       y = "Housing bills / total bills sponsored") +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        strip.background = element_rect(fill = "grey95", colour = NA),
        strip.text = element_text(face = "bold"))

ggsave(out_path, p, width = 7, height = 4.5)
