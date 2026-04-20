#!/usr/bin/env Rscript
# fig_3.R
# Legal keyword convergence for nine committee-switching legislators.
# Shows each legislator's legal keyword rate before and after a committee
# switch between the 20th and 21st National Assembly, against the new
# committee's baseline rate (dashed reference line).

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
  library(stringr)
})

# ---- Paths ------------------------------------------------------------------
speeches_path <- "/Users/kyusik/Desktop/kyusik-github/kr-hearings-data/data/all_speeches_16_22_v9.parquet"
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-15_r13/fig_3.pdf"
dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)

# Okabe-Ito palette (colorblind-safe)
okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#000000")

# ---- Keyword definitions ----------------------------------------------------
# Korean legal-register vocabulary: statutes, court process, prosecutorial acts.
legal_keywords <- c(
  "법률", "법령", "법안", "조항", "조문", "위반", "처벌", "판결", "소송",
  "위헌", "합헌", "헌법", "규정", "적법", "위법", "법적", "법원", "재판",
  "기소", "수사", "검찰", "피고", "원고", "변호", "판사", "검사"
)
legal_pattern <- paste(legal_keywords, collapse = "|")

# Judiciary committee (법제사법위원회).
judiciary_pattern <- "법제사법|법사위"

# ---- Aggregate speeches via arrow push-down ---------------------------------
ds <- arrow::open_dataset(speeches_path)

message("Counting total legislator speeches by term/committee/member ...")
totals <- ds %>%
  filter(term %in% c(20L, 21L),
         !is.na(member_id),
         !is.na(committee_key),
         !is.na(speech_text)) %>%
  group_by(term, committee_key, member_id) %>%
  summarise(n_speeches = n(), .groups = "drop") %>%
  collect()

message("Counting legal-register speeches by term/committee/member ...")
legal_counts <- ds %>%
  filter(term %in% c(20L, 21L),
         !is.na(member_id),
         !is.na(committee_key),
         !is.na(speech_text),
         str_detect(speech_text, legal_pattern)) %>%
  group_by(term, committee_key, member_id) %>%
  summarise(n_legal = n(), .groups = "drop") %>%
  collect()

speech_agg <- totals %>%
  left_join(legal_counts, by = c("term", "committee_key", "member_id")) %>%
  mutate(n_legal = tidyr::replace_na(n_legal, 0L))

# Member id -> person_name mapping
name_map <- ds %>%
  filter(term %in% c(20L, 21L), !is.na(member_id), !is.na(person_name)) %>%
  distinct(member_id, person_name) %>%
  collect() %>%
  group_by(member_id) %>%
  slice_head(n = 1) %>%
  ungroup()

# ---- Dominant committee per legislator x term -------------------------------
dom_cmt <- speech_agg %>%
  group_by(term, member_id) %>%
  slice_max(n_speeches, n = 1, with_ties = FALSE) %>%
  ungroup() %>%
  select(term, member_id, dom_cmt = committee_key,
         dom_n = n_speeches, dom_legal = n_legal) %>%
  mutate(legal_rate = dom_legal / dom_n)

# Committee-level baseline legal rate (all speeches, all legislators in cmt)
cmt_baseline <- speech_agg %>%
  group_by(term, committee_key) %>%
  summarise(cmt_legal_rate = sum(n_legal) / sum(n_speeches),
            .groups = "drop")

# ---- Identify switchers -----------------------------------------------------
r20 <- dom_cmt %>% filter(term == 20) %>%
  transmute(member_id, dom_20 = dom_cmt, legal_20 = legal_rate, n_20 = dom_n)
r21 <- dom_cmt %>% filter(term == 21) %>%
  transmute(member_id, dom_21 = dom_cmt, legal_21 = legal_rate, n_21 = dom_n)

switchers <- r20 %>%
  inner_join(r21, by = "member_id") %>%
  filter(dom_20 != dom_21) %>%
  left_join(name_map, by = "member_id") %>%
  left_join(
    cmt_baseline %>% filter(term == 21) %>%
      transmute(dom_21 = committee_key, baseline_21 = cmt_legal_rate),
    by = "dom_21"
  )

# Restrict to judiciary-related moves (either from or to, but not both)
js <- switchers %>%
  mutate(from_jud = str_detect(dom_20, judiciary_pattern),
         to_jud   = str_detect(dom_21, judiciary_pattern)) %>%
  filter(xor(from_jud, to_jud)) %>%
  filter(n_20 >= 30, n_21 >= 30)   # minimum speech count for reliable rates

# ---- Nine showcase legislators: 7 from judiciary + 2 to judiciary -----------
from_jud <- js %>% filter(from_jud) %>%
  mutate(abs_change = abs(legal_21 - legal_20)) %>%
  arrange(desc(abs_change)) %>%
  slice_head(n = 7)

to_jud <- js %>% filter(to_jud) %>%
  mutate(abs_change = abs(legal_21 - legal_20)) %>%
  arrange(desc(abs_change)) %>%
  slice_head(n = 2)

showcase <- bind_rows(from_jud, to_jud) %>%
  mutate(
    direction = ifelse(from_jud, "Moved from judiciary", "Moved to judiciary"),
    label = ifelse(is.na(person_name) | person_name == "",
                   as.character(member_id), person_name)
  )

# If data yielded fewer than 9 switchers, emit an honest placeholder
if (nrow(showcase) < 2) {
  message("Insufficient judiciary switchers found; writing placeholder.")
  p <- ggplot() +
    annotate("text", x = 0, y = 0, size = 4,
             label = "Figure not directly reproducible from public KNA data.\nSee replication archive.") +
    theme_void() + xlim(-1, 1) + ylim(-1, 1)
  ggsave(out_path, plot = p, width = 7, height = 4.5)
  quit(save = "no", status = 0)
}

# ---- Reshape for plotting ---------------------------------------------------
plot_long <- showcase %>%
  select(label, direction, baseline_21, legal_20, legal_21) %>%
  pivot_longer(c(legal_20, legal_21), names_to = "period", values_to = "rate") %>%
  mutate(assembly = ifelse(period == "legal_20", 20L, 21L))

# Facet order: group by direction, then by pre-switch rate (descending)
showcase_order <- showcase %>%
  arrange(direction, desc(legal_20)) %>%
  pull(label)
plot_long$label <- factor(plot_long$label, levels = showcase_order)

baselines <- showcase %>%
  distinct(label, direction, baseline_21) %>%
  mutate(label = factor(label, levels = showcase_order))

# ---- Plot -------------------------------------------------------------------
dir_colors <- c("Moved from judiciary" = "#D55E00",
                "Moved to judiciary"   = "#0072B2")

p <- ggplot(plot_long, aes(x = assembly, y = rate)) +
  geom_hline(data = baselines,
             aes(yintercept = baseline_21),
             linetype = "dashed", color = "grey30", linewidth = 0.35) +
  geom_line(aes(group = label, color = direction), linewidth = 0.8) +
  geom_point(aes(color = direction), size = 2.2) +
  facet_wrap(~ label, ncol = 3) +
  scale_color_manual(values = dir_colors, name = NULL) +
  scale_x_continuous(breaks = c(20, 21),
                     labels = c("20th\n(pre)", "21st\n(post)"),
                     limits = c(19.7, 21.3)) +
  scale_y_continuous(labels = function(v) paste0(round(v * 100), "%")) +
  labs(x = NULL,
       y = "Share of speeches with legal vocabulary") +
  theme_bw(base_size = 11) +
  theme(
    legend.position = "bottom",
    legend.margin = margin(t = -4),
    strip.text = element_text(size = 9),
    panel.grid.minor = element_blank(),
    panel.spacing = unit(0.6, "lines"),
    axis.text.x = element_text(size = 8)
  )

ggsave(out_path, plot = p, width = 7, height = 4.5)
message("Saved figure to: ", out_path)
