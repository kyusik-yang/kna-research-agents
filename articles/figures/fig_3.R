# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 3: Floor rejections across assemblies
library(arrow); library(dplyr); library(ggplot2)
DATA <- "/Users/kyusik/Desktop/kyusik-github/kna/data/processed"
compute_rejections <- function(assembly) {
  f <- file.path(DATA, sprintf("master_bills_%d.parquet", assembly))
  if (!file.exists(f)) return(NULL)
  b <- read_parquet(f)
  n_rejected <- sum(b$proc_rslt == "부결", na.rm = TRUE)
  n_total <- nrow(b)
  data.frame(assembly = assembly, rejected = n_rejected,
             total = n_total, rate = n_rejected / n_total * 100)
}
df <- bind_rows(lapply(17:22, compute_rejections))
ggplot(df, aes(x = factor(assembly), y = rejected)) +
  geom_col(fill = "#D55E00", width = 0.6) +
  geom_text(aes(label = rejected), vjust = -0.5, size = 3.5) +
  labs(x = "Assembly", y = "Bills Rejected on Floor",
       title = NULL) +
  theme_bw(base_size = 11) +
  scale_y_continuous(limits = c(0, 40))
ggsave("/Users/kyusik/Desktop/kyusik-github/kna-research-agents/articles/figures/fig_3.pdf", width = 7, height = 4.5)
