# Auto-generated figure for article
Sys.setenv(KBL_DATA = "/Users/kyusik/kna/data/processed")
# Figure 1: DPK Dissent Trajectory on Property-Tax Votes
library(ggplot2)

votes <- data.frame(
  vote_num = 1:5,
  label = c("Jul 2020\n(Tax Hike)", "Dec 2020\n(Amendment)",
            "Aug 2021\n(Adjustment)", "Jul 2022\n(Tax Cut)",
            "Mar 2023\n(Revision)"),
  dissent_pct = c(0.7, 0.0, 8.8, 37.3, 28.7),
  n_present = c(149, 151, 125, 134, 115)
)

votes$n_dissent <- round(votes$dissent_pct / 100 * votes$n_present)
votes$ci_low <- mapply(function(x, n) {
  if (x == 0) return(0)
  binom.test(x, n)$conf.int[1] * 100
}, votes$n_dissent, votes$n_present)
votes$ci_high <- mapply(function(x, n) {
  binom.test(x, n)$conf.int[2] * 100
}, votes$n_dissent, votes$n_present)

votes$label <- factor(votes$label, levels = votes$label)

ggplot(votes, aes(x = label, y = dissent_pct)) +
  geom_pointrange(aes(ymin = ci_low, ymax = ci_high), size = 0.7) +
  geom_hline(yintercept = 5, linetype = "dashed", color = "gray50") +
  annotate("text", x = 0.7, y = 7, label = "5% baseline",
           size = 3, color = "gray40", hjust = 0) +
  labs(x = NULL, y = "DPK Dissent Rate (%)",
       caption = "Note: 95% exact binomial confidence intervals.") +
  scale_y_continuous(limits = c(0, 55), breaks = seq(0, 50, 10)) +
  theme_bw(base_size = 11) +
  theme(axis.text.x = element_text(size = 9))

ggsave("/Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents/articles/figures/fig_1.pdf", width = 7, height = 4.5)
