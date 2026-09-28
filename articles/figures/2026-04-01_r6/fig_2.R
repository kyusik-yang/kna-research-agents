# Fig 2 (Version 2, 2026-09-27): Female x SMD interaction by Assembly, 20th-22nd,
# without a seniority control, with the Version 1 indicator (member-file
# `reelection`, a lifetime term count), and with seniority at the Assembly.
# Specification of Table 4: bill-level LPM of passage with party fixed effects,
# SE clustered by lead sponsor, 95 percent intervals.
# Sample: member bills (ppsr_kind 의원) whose lead sponsor is in that Assembly's
# member file.
#
# Seniority at the Assembly follows kna_seniority.derive() in the repository
# root: with L the lifetime count, n the number of member files 17-22 the member
# appears in and k the rank of Assembly a among them, the term number at a is
# L - n + k. Multi-term means a term number above 1.
#
# Version 1 of this script estimated each Assembly without fixed effects, with
# OLS standard errors, and used only the lifetime indicator.

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(ggplot2)
  library(fixest)
})

data_dir <- Sys.getenv("KNA_DATA_V060")  # published figure: pinned to the kna v0.6.0 data
if (!dir.exists(data_dir)) stop("KNA_DATA_V060 must name the data/processed folder of kna v0.6.0. ",
                             "Run scripts/setup_kna_v060.sh (see KNA_070_PUBLISHED.md).")
out_path <- "articles/figures/2026-04-01_r6/fig_2.pdf"

okabe_ito <- c("#E69F00", "#56B4E9", "#009E73", "#0072B2", "#D55E00", "#CC79A7", "#000000")

lifetime_count <- function(x) {
  x <- trimws(as.character(x))
  out <- suppressWarnings(as.integer(sub("\\s*\uc120$", "", x)))
  out[x == "\ucd08\uc120"] <- 1L
  out[x == "\uc7ac\uc120"] <- 2L
  out
}

# --- Member files 17-22 and the term number at each Assembly ---------------
members <- bind_rows(lapply(17:22, function(a) {
  read_parquet(file.path(data_dir, sprintf("members_%d.parquet", a)),
               col_select = c("mona_cd", "sex", "election_type", "party", "reelection")) %>%
    mutate(assembly = a)
})) %>%
  mutate(L = lifetime_count(reelection)) %>%
  arrange(mona_cd, assembly) %>%
  group_by(mona_cd) %>%
  mutate(n_files = n(), k = row_number(), term_number = L - n_files + k) %>%
  ungroup() %>%
  mutate(
    female = as.numeric(sex == "\uc5ec"),
    smd = as.numeric(election_type == "\uc9c0\uc5ed\uad6c"),
    multi_life = as.numeric(reelection != "\ucd08\uc120"),
    multi_asm = as.numeric(term_number > 1)
  )
stopifnot(!any(is.na(members$term_number)), all(members$term_number >= 1))

# --- Bills and models -------------------------------------------------------
rows <- list()
for (a in 20:22) {
  bills <- read_parquet(file.path(data_dir, sprintf("master_bills_%d.parquet", a)),
                        col_select = c("bill_id", "ppsr_kind", "rst_mona_cd", "passed")) %>%
    filter(ppsr_kind == "\uc758\uc6d0", !is.na(rst_mona_cd), rst_mona_cd != "") %>%
    mutate(passed = as.numeric(passed))
  df <- bills %>%
    inner_join(members %>% filter(assembly == a), by = c("rst_mona_cd" = "mona_cd"))

  specs <- list(
    "No seniority control" = passed ~ female * smd | party,
    "Version 1 indicator (lifetime count)" = passed ~ female * smd + multi_life | party,
    "Seniority at the Assembly" = passed ~ female * smd + multi_asm | party
  )
  for (lab in names(specs)) {
    m <- feols(specs[[lab]], data = df, cluster = ~rst_mona_cd,
               ssc = ssc(adj = TRUE, fixef.K = "none", cluster.adj = TRUE))
    ct <- coeftable(m)
    rows[[length(rows) + 1]] <- data.frame(
      assembly = a, spec = lab, n = nobs(m),
      estimate = unname(ct["female:smd", "Estimate"]),
      se = unname(ct["female:smd", "Std. Error"])
    )
  }
}

plot_df <- bind_rows(rows) %>%
  mutate(
    ci_low = estimate - qnorm(0.975) * se,
    ci_high = estimate + qnorm(0.975) * se,
    assembly_lbl = factor(c("20" = "20th Assembly", "21" = "21st Assembly", "22" = "22nd Assembly")[as.character(assembly)],
                          levels = c("20th Assembly", "21st Assembly", "22nd Assembly")),
    spec = factor(spec, levels = c("No seniority control", "Version 1 indicator (lifetime count)",
                                   "Seniority at the Assembly"))
  )
print(plot_df %>% mutate(across(c(estimate, se, ci_low, ci_high), ~ round(.x, 3))))

p <- ggplot(plot_df, aes(x = assembly_lbl, y = estimate, color = spec, shape = spec, group = spec)) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "grey40") +
  geom_pointrange(aes(ymin = ci_low, ymax = ci_high),
                  position = position_dodge(width = 0.55), size = 0.45, linewidth = 0.6) +
  scale_color_manual(values = c("No seniority control" = okabe_ito[5],
                                "Version 1 indicator (lifetime count)" = okabe_ito[1],
                                "Seniority at the Assembly" = okabe_ito[4]),
                     name = NULL) +
  scale_shape_manual(values = c("No seniority control" = 16,
                                "Version 1 indicator (lifetime count)" = 15,
                                "Seniority at the Assembly" = 17),
                     name = NULL) +
  labs(x = NULL, y = "Female x SMD interaction (LPM, party FE)") +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom",
        panel.grid.minor = element_blank(),
        panel.grid.major.x = element_blank()) +
  guides(color = guide_legend(nrow = 1), shape = guide_legend(nrow = 1))

dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)
pdf(out_path, width = 7, height = 4.5, useDingbats = FALSE)
print(p)
invisible(dev.off())
cat("Wrote:", out_path, "\n")
