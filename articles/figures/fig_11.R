#!/usr/bin/env Rscript

# fig_11.R
# Single-line plot: share of member-sponsored bills containing
# gender-equality keywords across the 17th-22nd Assemblies.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
})

# Okabe-Ito colorblind-safe palette
okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#000000")

data_dir <- "/Users/kyusik/kna/data/processed/"
out_path <- "/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_11.pdf"

# Load member info (17-22)
members <- read_parquet(file.path(data_dir, "member_info_17_22.parquet")) |>
  select(mona_cd, assembly, gender, election_type, reelection) |>
  distinct(mona_cd, assembly, .keep_all = TRUE)

# Load and stack bills 17-22
assemblies <- 17:22
bills_list <- lapply(assemblies, function(a) {
  fp <- file.path(data_dir, sprintf("master_bills_%d.parquet", a))
  read_parquet(fp)
})
bills <- bind_rows(bills_list)

# Filter to member-sponsored bills
bills_member <- bills |>
  filter(ppsr_kind == "의원")

# Join members to bills (rst_mona_cd = mona_cd AND age = assembly)
bills_joined <- bills_member |>
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "age" = "assembly"))

# Gender-equality keyword detection
# Search across plausible text columns (bill name, summary, content) if present
text_cols <- intersect(c("bill_name", "summary", "proposal_reason",
                         "main_content", "bill_kind_nm", "bill_summary",
                         "ppsl_rsn", "main_cnt", "summary_text"),
                       colnames(bills_joined))

gender_keywords <- paste(c(
  "성평등", "양성평등", "성차별", "여성차별", "남녀평등",
  "성별 격차", "성별격차", "유리천장", "여성가족", "여성정책",
  "성희롱", "성폭력", "성인지", "여성고용", "모성보호",
  "육아휴직", "출산휴가", "경력단절여성", "여성권익"
), collapse = "|")

if (length(text_cols) == 0) {
  # Fallback: try any character column
  text_cols <- names(bills_joined)[sapply(bills_joined, is.character)]
}

# Build a combined text field for keyword search
combined_text <- do.call(paste, c(lapply(text_cols, function(c) {
  x <- bills_joined[[c]]
  ifelse(is.na(x), "", as.character(x))
}), sep = " "))

bills_joined$has_gender_kw <- grepl(gender_keywords, combined_text)

# Compute share by assembly
share_df <- bills_joined |>
  group_by(age) |>
  summarise(
    n_bills = n(),
    n_gender = sum(has_gender_kw, na.rm = TRUE),
    share_pct = 100 * n_gender / n_bills,
    .groups = "drop"
  ) |>
  arrange(age)

print(share_df)

# Plot
p <- ggplot(share_df, aes(x = factor(age), y = share_pct, group = 1)) +
  geom_line(color = okabe_ito[4], linewidth = 0.9) +
  geom_point(color = okabe_ito[4], size = 2.4) +
  scale_y_continuous(
    labels = function(x) paste0(format(x, nsmall = 2), "%")
  ) +
  labs(
    x = "National Assembly",
    y = "Share of member bills with gender-equality keywords"
  ) +
  theme_bw(base_size = 11)

ggsave(out_path, plot = p, width = 7, height = 4.5)
