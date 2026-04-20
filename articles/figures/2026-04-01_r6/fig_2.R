# Fig 2: Female x SMD interaction coefficients by assembly, with and without seniority control.
# Computed from master_bills + members parquets for 20th, 21st, 22nd assemblies.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

data_dir <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
out_path <- "/Users/kyusik/Desktop/kyusik-claude/kna-research-agents/articles/figures/2026-04-01_r6/fig_2.pdf"

okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2", "#D55E00", "#CC79A7", "#000000")

assemblies <- c(20, 21, 22)

rows <- list()

for (a in assemblies) {
  bills_path <- file.path(data_dir, paste0("master_bills_", a, ".parquet"))
  members_path <- file.path(data_dir, paste0("members_", a, ".parquet"))

  if (!file.exists(bills_path) || !file.exists(members_path)) next

  bills <- read_parquet(bills_path) %>%
    filter(ppsr_kind == "\uc758\uc6d0",
           !is.na(rst_mona_cd),
           !is.na(passed)) %>%
    mutate(passed_num = as.numeric(as.integer(passed))) %>%
    select(bill_id, rst_mona_cd, passed_num)

  members <- read_parquet(members_path) %>%
    select(mona_cd, sex, election_type, reelection) %>%
    distinct(mona_cd, .keep_all = TRUE) %>%
    mutate(
      female = as.numeric(sex == "\uc5ec"),
      smd = as.numeric(election_type == "\uc9c0\uc5ed\uad6c"),
      multi_term = as.numeric(!is.na(reelection) & reelection != "\ucd08\uc120")
    )

  df <- bills %>%
    inner_join(members, by = c("rst_mona_cd" = "mona_cd")) %>%
    filter(!is.na(female), !is.na(smd), !is.na(multi_term))

  if (nrow(df) < 100) next

  m1 <- lm(passed_num ~ female * smd, data = df)
  m2 <- lm(passed_num ~ female * smd + multi_term, data = df)

  extract_int <- function(model, label) {
    s <- summary(model)$coefficients
    tname <- "female:smd"
    if (!(tname %in% rownames(s))) return(NULL)
    data.frame(
      assembly = a,
      spec = label,
      estimate = unname(s[tname, "Estimate"]),
      se = unname(s[tname, "Std. Error"]),
      stringsAsFactors = FALSE
    )
  }

  r1 <- extract_int(m1, "Without seniority")
  r2 <- extract_int(m2, "With seniority")
  if (!is.null(r1)) rows[[length(rows) + 1]] <- r1
  if (!is.null(r2)) rows[[length(rows) + 1]] <- r2
}

if (length(rows) == 0) {
  plot_df <- data.frame()
  p <- ggplot() +
    annotate("text", x = 0, y = 0, size = 4,
             label = "Figure not directly reproducible from public KNA data.\nSee replication archive.") +
    theme_void() + xlim(-1, 1) + ylim(-1, 1)
} else {
  plot_df <- bind_rows(rows) %>%
    mutate(
      ci_low = estimate - 1.96 * se,
      ci_high = estimate + 1.96 * se,
      assembly_lbl = factor(paste0(assembly, "th Assembly"),
                            levels = paste0(sort(unique(assembly)), "th Assembly")),
      spec = factor(spec, levels = c("Without seniority", "With seniority"))
    )

  p <- ggplot(plot_df,
              aes(x = assembly_lbl, y = estimate,
                  color = spec, shape = spec, group = spec)) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "grey40") +
    geom_pointrange(aes(ymin = ci_low, ymax = ci_high),
                    position = position_dodge(width = 0.45),
                    size = 0.6, fatten = 3) +
    scale_color_manual(values = c("Without seniority" = okabe_ito[5],
                                  "With seniority" = okabe_ito[4]),
                       name = NULL) +
    scale_shape_manual(values = c("Without seniority" = 16,
                                  "With seniority" = 17),
                       name = NULL) +
    labs(x = NULL,
         y = "Female x SMD interaction coefficient") +
    theme_bw(base_size = 11) +
    theme(
      legend.position = "bottom",
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank()
    )
}

dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)
ggsave(out_path, plot = p, width = 7, height = 4.5)
