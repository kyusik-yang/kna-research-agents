# fig_10.R
# Four-line plot of bill passage rates by gender and mandate type
# across the 17th to 22nd Assemblies.

library(arrow)
library(dplyr)
library(ggplot2)

data_dir <- "/Users/kyusik/kna/data/processed/"
out_path <- "/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_10.pdf"

# Load member info
members <- read_parquet(file.path(data_dir, "member_info_17_22.parquet")) |>
  select(mona_cd, assembly, gender, election_type, reelection)

# Load all assemblies of bills
assemblies <- 17:22
bills_list <- lapply(assemblies, function(a) {
  read_parquet(file.path(data_dir, paste0("master_bills_", a, ".parquet")))
})
bills <- bind_rows(bills_list)

# Filter member-sponsored bills and join with member info
bills_member <- bills |>
  filter(ppsr_kind == "의원") |>
  inner_join(members, by = c("rst_mona_cd" = "mona_cd", "age" = "assembly"))

# Compute passage rates by assembly, gender, and mandate type
plot_df <- bills_member |>
  filter(!is.na(gender), !is.na(election_type), gender %in% c("남", "여"),
         election_type %in% c("비례대표", "지역구")) |>
  group_by(age, gender, election_type) |>
  summarise(passage_rate = mean(passed, na.rm = TRUE),
            n_bills = n(),
            .groups = "drop") |>
  mutate(
    gender_en = ifelse(gender == "여", "Women", "Men"),
    mandate_en = ifelse(election_type == "지역구", "SMD", "PR"),
    group = paste(gender_en, mandate_en, sep = " - "),
    assembly_label = paste0(age, "th")
  )

# Order groups for legend
plot_df$group <- factor(plot_df$group,
                        levels = c("Women - SMD", "Men - SMD",
                                   "Women - PR", "Men - PR"))

# Okabe-Ito colorblind palette
okabe_ito <- c(
  "Women - SMD" = "#D55E00",
  "Men - SMD"   = "#0072B2",
  "Women - PR"  = "#E69F00",
  "Men - PR"    = "#56B4E9"
)

p <- ggplot(plot_df,
            aes(x = age, y = passage_rate,
                color = group, linetype = group, shape = group)) +
  geom_line(linewidth = 0.8) +
  geom_point(size = 2.4) +
  scale_color_manual(values = okabe_ito) +
  scale_linetype_manual(values = c("Women - SMD" = "solid",
                                   "Men - SMD"   = "solid",
                                   "Women - PR"  = "dashed",
                                   "Men - PR"    = "dashed")) +
  scale_shape_manual(values = c("Women - SMD" = 16,
                                "Men - SMD"   = 17,
                                "Women - PR"  = 15,
                                "Men - PR"    = 18)) +
  scale_x_continuous(breaks = assemblies,
                     labels = paste0(assemblies, "th")) +
  scale_y_continuous(labels = scales::percent_format(accuracy = 1)) +
  labs(x = "Assembly",
       y = "Bill passage rate",
       color = NULL, linetype = NULL, shape = NULL) +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom",
        legend.box = "horizontal",
        panel.grid.minor = element_blank())

ggsave(out_path, plot = p, width = 7, height = 4.5)
