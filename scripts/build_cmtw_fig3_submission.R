library(ggplot2)
library(patchwork)
library(dplyr)
library(tidyr)
library(scales)
library(grid)

args_all <- commandArgs(trailingOnly = FALSE)
script_arg <- args_all[grep("--file=", args_all)]
base_dir <- normalizePath(dirname(sub("--file=", "", script_arg)), winslash = "/", mustWork = TRUE)
artifact_dir <- normalizePath(file.path(base_dir, ".."), winslash = "/", mustWork = TRUE)
source_dir <- normalizePath(file.path(artifact_dir, "figure-source-data"), winslash = "/", mustWork = TRUE)
output_dir <- file.path(artifact_dir, "reproduced", "paper-figures")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

pal <- c(
  ink = "#202A35",
  slate = "#5E6B78",
  slate_mid = "#95A2AE",
  neutral = "#DDE3E8",
  neutral_light = "#F6F8F9",
  teal = "#148C8F",
  teal_mid = "#78BFC0",
  teal_light = "#D7EEEE",
  coral = "#CC4D4E",
  coral_mid = "#E39A9B",
  coral_light = "#F5DADB",
  ochre = "#D9951E",
  ochre_mid = "#E8BA62",
  ochre_light = "#F8E9CB",
  navy = "#355C7D"
)

theme_cmtw <- function(base_size = 7.3) {
  theme_classic(base_size = base_size, base_family = "Arial") +
    theme(
      axis.line = element_line(linewidth = 0.35, colour = pal[["ink"]]),
      axis.ticks = element_line(linewidth = 0.35, colour = pal[["ink"]]),
      axis.text = element_text(colour = pal[["ink"]]),
      axis.title = element_text(colour = pal[["ink"]]),
      legend.position = "none",
      panel.grid = element_blank(),
      plot.margin = margin(3, 3, 3, 3, "pt"),
      plot.tag = element_text(family = "Arial", face = "bold", size = 9,
                              colour = pal[["ink"]]),
      plot.tag.position = c(0, 1),
      strip.background = element_blank(),
      strip.text = element_text(face = "bold", colour = pal[["slate"]], size = 6.8)
    )
}

save_bundle <- function(plot, stem, width_mm, height_mm, dpi = 600) {
  width_in <- width_mm / 25.4
  height_in <- height_mm / 25.4
  ggsave(file.path(output_dir, paste0(stem, ".pdf")), plot,
         width = width_in, height = height_in, device = cairo_pdf,
         family = "Arial", bg = "white")
  ggsave(file.path(output_dir, paste0(stem, ".svg")), plot,
         width = width_in, height = height_in, device = svglite::svglite,
         bg = "white")
  ggsave(file.path(output_dir, paste0(stem, ".png")), plot,
         width = width_in, height = height_in, device = ragg::agg_png,
         dpi = 420, bg = "white")
  ggsave(file.path(output_dir, paste0(stem, ".tiff")), plot,
         width = width_in, height = height_in, device = ragg::agg_tiff,
         dpi = dpi, compression = "lzw", bg = "white")
}

status_fill <- c(PASS = unname(pal[["teal_light"]]), FAIL = unname(pal[["coral_light"]]))
status_text <- c(PASS = unname(pal[["teal"]]), FAIL = unname(pal[["coral"]]))

# -----------------------------------------------------------------------------
# Figure 3 - contract outcomes and the measured recomputation price
# -----------------------------------------------------------------------------
fig3_matrix <- tibble::tribble(
  ~policy, ~obligation, ~status, ~label,
  "Preserve\nold view", "Recorded paths", "FAIL", "FAIL\n8/8 remain",
  "Preserve\nold view", "Canary leakage", "FAIL", "FAIL\n10/24 leak",
  "Preserve\nold view", "Safe context", "PASS", "PASS\n8/8 retained",
  "Invalidate\nwhole view", "Recorded paths", "PASS", "PASS\n0/8 remain",
  "Invalidate\nwhole view", "Canary leakage", "PASS", "PASS\n0/24 leak",
  "Invalidate\nwhole view", "Safe context", "FAIL", "FAIL\n0/8 retained"
)

# The final row is appended separately to keep tribble columns exact.
fig3_matrix <- bind_rows(
  fig3_matrix %>% filter(!(policy == "Selective\nrebuild" & obligation == "Recorded paths")),
  tibble(
    policy = rep("Selective\nrebuild", 3),
    obligation = c("Recorded paths", "Canary leakage", "Safe context"),
    status = rep("PASS", 3),
    label = c("PASS\n0/8 remain", "PASS\n0/24 leak", "PASS\n8/8 retained")
  )
) %>%
  mutate(
    policy = factor(policy, levels = rev(c("Preserve\nold view", "Invalidate\nwhole view", "Selective\nrebuild"))),
    obligation = factor(obligation, levels = c("Recorded paths", "Canary leakage", "Safe context"))
  )

p3a <- ggplot(fig3_matrix, aes(obligation, policy)) +
  geom_tile(aes(fill = status), colour = "white", linewidth = 1.0) +
  geom_text(aes(label = label, colour = status), family = "Arial",
            fontface = "bold", size = 2.45, lineheight = 0.88) +
  annotate("rect", xmin = 0.50, xmax = 3.50, ymin = 0.50, ymax = 1.50,
           fill = NA, colour = pal[["teal"]], linewidth = 0.65) +
  scale_fill_manual(values = status_fill) +
  scale_colour_manual(values = status_text) +
  scale_x_discrete(labels = c("Recorded paths" = "recorded paths\nremaining",
                              "Canary leakage" = "exact canary\nleakage",
                              "Safe context" = "safe context\nretained"),
                   position = "top") +
  labs(x = NULL, y = NULL, tag = "a") +
  theme_cmtw(7.3) +
  theme(
    axis.line = element_blank(), axis.ticks = element_blank(),
    axis.text.x = element_text(size = 6.7, lineheight = 0.88, colour = pal[["slate"]]),
    axis.text.y = element_text(size = 6.9, lineheight = 0.90, colour = pal[["ink"]]),
    plot.margin = margin(8, 2, 2, 4, "pt")
  )

lat <- read.csv(file.path(source_dir, "fig3-rebuild-latency-seeds.csv"))
cluster <- lat %>% filter(seconds < 4)
all_med <- median(lat$seconds)
all_iqr <- quantile(lat$seconds, c(0.25, 0.75))
cluster_min <- min(cluster$seconds)
cluster_max <- max(cluster$seconds)
lat <- lat %>% arrange(seconds) %>% mutate(rug_y = 0.38 + (row_number() %% 3) * 0.07)

p3b_overview <- ggplot(lat, aes(seconds, rug_y)) +
  annotate("rect", xmin = cluster_min, xmax = cluster_max,
           ymin = 0.25, ymax = 0.72, fill = pal[["ochre_light"]], colour = NA) +
  geom_segment(aes(xend = seconds, y = rug_y - 0.07, yend = rug_y + 0.07),
               linewidth = 0.42, colour = pal[["ochre"]]) +
  annotate("text", x = 3.69, y = 0.94, label = "19/20 seeds",
           family = "Arial", size = 2.15, colour = pal[["slate"]]) +
  annotate("text", x = 6.263, y = 0.90, label = "1 seed\n6.263 s",
           family = "Arial", size = 2.15, lineheight = 0.86, colour = pal[["ochre"]]) +
  scale_x_continuous(limits = c(3.50, 6.50), breaks = c(3.5, 4.0, 5.0, 6.0, 6.5)) +
  coord_cartesian(ylim = c(0.12, 1.02), clip = "off") +
  labs(x = NULL, y = NULL, tag = "b") +
  theme_cmtw(7.2) +
  theme(
    axis.line.y = element_blank(), axis.ticks.y = element_blank(), axis.text.y = element_blank(),
    plot.margin = margin(5, 4, 0, 4, "pt")
  )

p3b_zoom <- ggplot(cluster, aes(seconds, 0.48)) +
  annotate("rect", xmin = cluster_min, xmax = cluster_max,
           ymin = 0.20, ymax = 0.75, fill = pal[["ochre_light"]], colour = NA) +
  geom_segment(aes(xend = seconds, y = 0.31, yend = 0.64),
               linewidth = 0.42, colour = pal[["ochre"]]) +
  annotate("segment", x = all_iqr[[1]], xend = all_iqr[[2]],
           y = 0.84, yend = 0.84, linewidth = 1.6, lineend = "round",
           colour = pal[["ink"]]) +
  annotate("segment", x = all_med, xend = all_med,
           y = 0.72, yend = 0.96, linewidth = 0.50, colour = pal[["ink"]]) +
  annotate("text", x = 3.622, y = 1.08,
           label = "cluster detail: median 3.698 s; all-seed IQR 3.673-3.713 s",
           hjust = 0, family = "Arial", size = 2.05, colour = pal[["slate"]]) +
  scale_x_continuous(limits = c(3.62, 3.76), breaks = c(3.62, 3.66, 3.70, 3.74, 3.76)) +
  coord_cartesian(ylim = c(0.10, 1.10), clip = "off") +
  labs(x = "selective re-consolidation time per persona (s)", y = NULL) +
  theme_cmtw(7.1) +
  theme(axis.line.y = element_blank(), axis.ticks.y = element_blank(), axis.text.y = element_blank(),
        plot.margin = margin(0, 4, 2, 4, "pt"))

p3b <- p3b_overview / p3b_zoom + plot_layout(heights = c(0.78, 0.92))
fig3 <- p3a / p3b + plot_layout(heights = c(1.45, 1.02))
save_bundle(fig3, "cmtw-fig3-recorded-view-repair", 89, 86)

# This submission script intentionally stops after the adopted Figure 3.
quit(save = "no", status = 0)
