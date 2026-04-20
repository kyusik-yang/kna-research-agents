# fig_3.R
# Housing bill volume and passage rates across the 19th-22nd Assemblies.
# All numbers are computed from master_bills_{19-22}.parquet.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- Sys.getenv("KBL_DATA",
                      "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")

# ---- 1. Load bills for the 19th-22nd Assemblies ----------------------------
bills <- bind_rows(lapply(19:22, function(a) {
  read_parquet(file.path(data_dir, sprintf("master_bills_%d.parquet", a)))
}))

# ---- 2. Housing classification ---------------------------------------------
# Broad Korean housing / real-estate keyword set applied to bill title.
housing_pattern <- paste(
  "\uc8fc\ud0dd",       # 주택
  "\ubd80\ub3d9\uc0b0", # 부동산
  "\uc784\ub300",       # 임대
  "\uc804\uc138",       # 전세
  "\uc6d4\uc138",       # 월세
  "\uc7ac\uac1c\ubc1c", # 재개발
  "\uc7ac\uac74\ucd95", # 재건축
  "\uc8fc\uac70",       # 주거
  "\ud0dd\uc9c0",       # 택지
  "\ubd84\uc591",       # 분양
  "\uc784\ucc28",       # 임차
  "\uac74\ucd95",       # 건축
  sep = "|")

bills <- bills %>%
  mutate(
    is_housing = grepl(housing_pattern, bill_nm),
    passed_bin = ifelse(is.na(passed), 0, as.integer(passed))
  )

# ---- 3. Aggregate counts & passage rates -----------------------------------
agg <- bills %>%
  group_by(age, is_housing) %>%
  summarise(
    n_bills   = dplyr::n(),
    pass_rate = mean(passed_bin == 1),
    .groups   = "drop"
  ) %>%
  mutate(
    assembly = factor(age, levels = 19:22,
                      labels = c("19th", "20th", "21st", "22nd")),
    category = ifelse(is_housing, "Housing", "Non-housing")
  )

# Volume panel: housing only
panel_a <- agg %>%
  filter(is_housing) %>%
  transmute(
    assembly,
    category,
    panel = "(a) Housing bill volume",
    value = n_bills,
    label = formatC(n_bills, format = "d", big.mark = ",")
  )

# Passage-rate panel: housing vs non-housing
panel_b <- agg %>%
  transmute(
    assembly,
    category,
    panel = "(b) Passage rate",
    value = pass_rate * 100,
    label = sprintf("%.0f%%", pass_rate * 100)
  )

plot_df <- bind_rows(panel_a, panel_b) %>%
  mutate(panel = factor(panel,
                        levels = c("(a) Housing bill volume",
                                   "(b) Passage rate")))

# ---- 4. Plot ---------------------------------------------------------------
okabe <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
           "#D55E00", "#CC79A7", "#000000")

fill_map <- c("Housing" = okabe[5], "Non-housing" = okabe[2])

p <- ggplot(plot_df, aes(x = assembly, y = value,
                         fill = category, group = category)) +
  geom_col(position = position_dodge(width = 0.8),
           width = 0.7, colour = NA) +
  geom_text(aes(label = label),
            position = position_dodge(width = 0.8),
            vjust = -0.4, size = 3) +
  facet_wrap(~ panel, scales = "free_y") +
  scale_fill_manual(values = fill_map, name = NULL) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.18))) +
  labs(x = "National Assembly", y = NULL) +
  theme_bw(base_size = 11) +
  theme(
    legend.position   = "top",
    legend.margin     = margin(0, 0, 0, 0),
    panel.grid.minor  = element_blank(),
    panel.grid.major.x = element_blank(),
    strip.background  = element_rect(fill = "grey95", colour = NA),
    strip.text        = element_text(face = "bold", hjust = 0)
  )

# ---- 5. Save ---------------------------------------------------------------
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-05_r8/fig_3.pdf"
dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)
ggsave(out_path, p, width = 7, height = 4.5)
