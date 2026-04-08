# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 2: Absorption ratio over time
library(arrow); library(dplyr); library(ggplot2)
DATA <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
compute_ratio <- function(assembly) {
  f <- file.path(DATA, sprintf("master_bills_%d.parquet", assembly))
  if (!file.exists(f)) return(NULL)
  b <- read_parquet(f) |> filter(ppsr_kind == "의원")
  chair_b <- read_parquet(f) |> filter(ppsr_kind == "위원장")
  n_chair <- nrow(chair_b)
  n_absorbed <- sum(b$proc_rslt == "대안반영폐기", na.rm = TRUE)
  ratio <- ifelse(n_chair > 0, n_absorbed / n_chair, NA)
  pass_rate <- mean(chair_b$passed == 1, na.rm = TRUE) * 100
  data.frame(assembly = assembly, chair_bills = n_chair,
             absorbed = n_absorbed, ratio = ratio,
             pass_rate = pass_rate)
}
df <- bind_rows(lapply(17:22, compute_ratio))
ggplot(df, aes(x = factor(assembly), y = ratio)) +
  geom_col(fill = "#0072B2", width = 0.6) +
  geom_text(aes(label = sprintf("%.1f", ratio)), vjust = -0.5, size = 3.5) +
  labs(x = "Assembly", y = "Bills Absorbed per Chair Alternative",
       title = NULL) +
  theme_bw(base_size = 11) +
  scale_y_continuous(limits = c(0, 6))
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/fig_2.pdf", width = 7, height = 4.5)
