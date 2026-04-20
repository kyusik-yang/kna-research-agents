# fig_1.R
# Mean chief-sponsorship rate per member-month by assembly.
# Computed directly from master_bills_{17-22}.parquet and members_{17-22}.parquet.
#
# Definition (as used in the paper's continuer-pool discussion):
#   rate per member-month
#     = (# member-chief-sponsored bills in assembly)
#       / (# sitting members in assembly * # months the assembly ran)
#
# All numbers are computed from the parquet files - no hardcoded values.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- Sys.getenv("KBL_DATA", "/Users/kyusik/Desktop/kyusik-github/kna/data/processed")

out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-19_r19/fig_1.pdf"

assemblies <- 17:22

okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2",
               "#D55E00", "#CC79A7", "#000000")

compute_one <- function(a) {
  bills_path   <- file.path(data_dir, sprintf("master_bills_%d.parquet", a))
  members_path <- file.path(data_dir, sprintf("members_%d.parquet", a))
  if (!file.exists(bills_path) || !file.exists(members_path)) return(NULL)

  bills <- read_parquet(bills_path) %>%
    select(any_of(c("bill_id", "age", "ppsr_kind", "rst_mona_cd", "ppsl_dt")))
  members <- read_parquet(members_path) %>%
    select(any_of(c("mona_cd", "age")))

  # Keep member-sponsored (chief) rows only.
  chief <- bills %>%
    filter(!is.na(ppsr_kind), ppsr_kind == "\uc758\uc6d0") %>%
    filter(!is.na(rst_mona_cd), !is.na(ppsl_dt))

  if (nrow(chief) == 0) return(NULL)

  # Parse proposal date, drop unparseable rows.
  chief <- chief %>%
    mutate(ppsl_date = suppressWarnings(as.Date(ppsl_dt))) %>%
    filter(!is.na(ppsl_date))

  if (nrow(chief) == 0) return(NULL)

  # Month range: span of observed chief-sponsorship activity within the assembly.
  first_month <- as.Date(format(min(chief$ppsl_date), "%Y-%m-01"))
  last_month  <- as.Date(format(max(chief$ppsl_date), "%Y-%m-01"))
  month_seq <- seq(first_month, last_month, by = "month")
  n_months <- length(month_seq)

  # Roster size (unique mona_cd in that assembly).
  n_members <- members %>%
    filter(!is.na(mona_cd)) %>%
    distinct(mona_cd) %>%
    nrow()

  total_chief <- nrow(chief)
  rate <- total_chief / (n_members * n_months)

  data.frame(
    assembly    = a,
    n_members   = n_members,
    n_months    = n_months,
    total_chief = total_chief,
    mean_rate   = rate
  )
}

rows <- lapply(assemblies, compute_one)
df <- bind_rows(rows)

if (nrow(df) == 0) {
  # Honest placeholder - inputs missing.
  p <- ggplot() +
    annotate("text", x = 0, y = 0, size = 4,
             label = "Figure not directly reproducible from public KNA data.\nSee replication archive.") +
    theme_void() + xlim(-1, 1) + ylim(-1, 1)
  ggsave(out_path, p, width = 7, height = 4.5)
  quit(status = 0)
}

df <- df %>%
  arrange(assembly) %>%
  mutate(assembly_lab = paste0(assembly, "th"))

p <- ggplot(df, aes(x = factor(assembly, levels = sort(unique(assembly))),
                    y = mean_rate, group = 1)) +
  geom_line(color = okabe_ito[4], linewidth = 0.6) +
  geom_point(color = okabe_ito[4], size = 2.4) +
  geom_text(aes(label = sprintf("%.2f", mean_rate)),
            vjust = -0.9, size = 3, color = "grey20") +
  scale_x_discrete(labels = function(x) paste0(x, "th")) +
  scale_y_continuous(expand = expansion(mult = c(0.05, 0.18))) +
  labs(x = "Assembly",
       y = "Mean chief-sponsorship rate (bills per member-month)") +
  theme_bw(base_size = 11) +
  theme(panel.grid.minor = element_blank(),
        panel.grid.major.x = element_blank())

ggsave(out_path, p, width = 7, height = 4.5)
