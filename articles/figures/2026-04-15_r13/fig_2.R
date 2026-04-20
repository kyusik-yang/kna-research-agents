# fig_2.R
# Figure 2: Legal keyword rates by standing committee, 21st Assembly 국정감사
# Data source: all_speeches_16_22_v9.parquet (filter pushed down via arrow dataset)

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
  library(stringr)
  library(scales)
})

okabe <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
           "#D55E00", "#CC79A7", "#000000")

speeches_path <- "/Users/kyusik/Desktop/kyusik-github/kr-hearings-data/data/all_speeches_16_22_v9.parquet"
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-15_r13/fig_2.pdf"

# Korean legal-register vocabulary. The set captures the "legal style"
# discussed in the paper: court/prosecution/litigation/statutory language.
legal_keywords <- c(
  "법률", "법안", "법령", "법조항", "법원", "검찰", "검찰청",
  "소송", "판결", "판사", "검사", "변호사", "변호인",
  "기소", "구속", "수사", "재판", "헌법", "위헌",
  "형사", "민사", "처벌", "범죄", "고발", "고소",
  "영장", "압수수색", "압수", "구형", "형량",
  "유죄", "무죄", "증거", "증인", "피고", "피고인",
  "원고", "공소", "공판", "항소", "상고", "판례"
)
legal_pattern <- paste(legal_keywords, collapse = "|")

# Pushdown filter: read only what we need
ds <- open_dataset(speeches_path)

df <- ds %>%
  filter(term == 21L,
         hearing_type == "국정감사",
         role %in% c("legislator", "chair")) %>%
  select(committee, speech_text) %>%
  collect()

df <- df %>%
  filter(!is.na(committee),
         !is.na(speech_text),
         nchar(speech_text) >= 10) %>%
  mutate(has_legal = str_detect(speech_text, legal_pattern))

# Aggregate per standing committee. Require enough speech acts for a
# stable rate estimate.
committee_rates <- df %>%
  group_by(committee) %>%
  summarise(legal_rate = mean(has_legal),
            n_speeches = n(),
            .groups = "drop") %>%
  filter(n_speeches >= 200) %>%
  mutate(is_judiciary = str_detect(committee, "법제사법"))

# Non-judiciary baseline (dashed line)
nonjud_avg <- committee_rates %>%
  filter(!is_judiciary) %>%
  summarise(avg = mean(legal_rate)) %>%
  pull(avg)

# Short label for judiciary to keep legend semantics readable
committee_rates <- committee_rates %>%
  mutate(committee_lab = committee,
         fill_grp = ifelse(is_judiciary, "Judiciary", "Other standing committees"))

p <- ggplot(committee_rates,
            aes(x = reorder(committee_lab, legal_rate),
                y = legal_rate,
                fill = fill_grp)) +
  geom_col(width = 0.75) +
  geom_hline(yintercept = nonjud_avg,
             linetype = "dashed",
             color = "grey25",
             linewidth = 0.4) +
  annotate("text",
           x = 1,
           y = nonjud_avg,
           label = sprintf("Non-judiciary avg = %.1f%%", 100 * nonjud_avg),
           hjust = -0.05, vjust = -0.6,
           size = 3, color = "grey25") +
  scale_fill_manual(values = c("Judiciary" = okabe[5],
                               "Other standing committees" = okabe[4]),
                    name = NULL) +
  scale_y_continuous(labels = percent_format(accuracy = 1),
                     expand = expansion(mult = c(0, 0.05))) +
  coord_flip() +
  labs(x = NULL,
       y = "Share of speech acts containing legal vocabulary") +
  theme_bw(base_size = 11) +
  theme(panel.grid.major.y = element_blank(),
        panel.grid.minor = element_blank(),
        legend.position = "bottom",
        legend.margin = margin(t = -4))

ggsave(out_path, p, width = 7, height = 4.5)
