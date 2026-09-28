# fig_1.R - synthetic figure script
library(arrow)
DATA <- Sys.getenv("KBL_DATA")
bills <- read_parquet(file.path(DATA, "master_bills_21.parquet"))
ggsave("fig_1.pdf", width = 7, height = 4.5)
