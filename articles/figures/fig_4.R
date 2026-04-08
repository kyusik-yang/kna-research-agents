# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 4: Ruling-party passage advantage across assemblies
library(arrow); library(dplyr); library(ggplot2)
DATA <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
compute_gap <- function(assembly) {
  bf <- file.path(DATA, sprintf("master_bills_%d.parquet", assembly))
  mf <- file.path(DATA, sprintf("members_%d.parquet", assembly))
  if (!file.exists(bf) || !file.exists(mf)) return(NULL)
  b <- read_parquet(bf) |> filter(ppsr_kind == "의원")
  m <- read_parquet(mf) |> select(mona_cd, party)
  b <- left_join(b, m, by = c("rst_mona_cd" = "mona_cd"))
  ruling_parties <- switch(as.character(assembly),
    "17" = c("열린우리당", "한나라당")[1], "18" = c("한나라당", "새누리당"),
    "19" = c("새누리당"), "20" = c("더불어민주당"),
    "21" = c("더불어민주당"), "22" = c("국민의힘", "국민의미래"))
  b <- b |> mutate(ruling = party %in% ruling_parties)
  gap <- b |> filter(!is.na(ruling)) |> group_by(ruling) |>
    summarise(pass = mean(passed == 1, na.rm = TRUE), .groups = "drop")
  r <- gap$pass[gap$ruling == TRUE]
  o <- gap$pass[gap$ruling == FALSE]
  data.frame(assembly = assembly, gap_pp = (r - o) * 100,
             ruling_pass = r * 100, opp_pass = o * 100)
}
df <- bind_rows(lapply(17:22, compute_gap))
df$label <- c("Mixed\nchairs", "Ruling\nchairs", "Ruling\nchairs",
              "Mixed\nchairs", "DP\nchairs", "All opp\nchairs")
ggplot(df, aes(x = factor(assembly), y = gap_pp)) +
  geom_col(fill = ifelse(df$gap_pp >= 0, "#0072B2", "#D55E00"), width = 0.6) +
  geom_hline(yintercept = 0, linewidth = 0.4) +
  geom_text(aes(label = sprintf("%+.1f", gap_pp)),
            vjust = ifelse(df$gap_pp >= 0, -0.5, 1.5), size = 3.2) +
  labs(x = "Assembly", y = "Ruling-Party Advantage (pp)") +
  theme_bw(base_size = 11) +
  scale_y_continuous(limits = c(-5, 15))
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/fig_4.pdf", width = 7, height = 4.5)
