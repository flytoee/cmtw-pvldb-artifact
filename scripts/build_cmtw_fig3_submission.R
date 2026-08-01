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

lat <- read.csv(file.path(source_dir, "fig3-v6-rebuild-latency.csv"))
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
save_bundle(fig3, "cmtw-v10-fig3-contract-outcomes", 89, 86)

# This submission script intentionally stops after the adopted Figure 3.
quit(save = "no", status = 0)

# -----------------------------------------------------------------------------
# Figure 4 - semantic admission has no usable operating point
# -----------------------------------------------------------------------------
adm_agg <- tibble::tribble(
  ~model, ~obligation, ~correct, ~total,
  "Mistral 14B", "Quarantine contamination", 40, 40,
  "Mistral 14B", "Admit safe evolution", 28, 40,
  "LFM2 24B", "Quarantine contamination", 40, 40,
  "LFM2 24B", "Admit safe evolution", 3, 40,
  "Llama MoE", "Quarantine contamination", 0, 40,
  "Llama MoE", "Admit safe evolution", 40, 40
) %>%
  mutate(
    accuracy = correct / total,
    label = sprintf("%d/%d\n%s", correct, total, percent(accuracy, accuracy = 1)),
    model = factor(model, levels = c("Mistral 14B", "LFM2 24B", "Llama MoE")),
    obligation = recode(obligation,
                        `Quarantine contamination` = "quarantine\ncontamination",
                        `Admit safe evolution` = "admit safe\nevolution"),
    obligation = factor(obligation, levels = c("quarantine\ncontamination", "admit safe\nevolution"))
  )

assertion_cells <- adm_agg %>%
  select(model, obligation, correct, total) %>%
  tidyr::uncount(total, .id = "cell") %>%
  mutate(
    correct_flag = cell <= correct,
    cell_x = (cell - 1) %% 8 + 1,
    cell_y = 5 - floor((cell - 1) / 8)
  )

p4a <- ggplot(assertion_cells, aes(cell_x, cell_y)) +
  geom_tile(aes(fill = correct_flag), width = 0.94, height = 0.72,
            colour = "white", linewidth = 0.16) +
  geom_text(data = adm_agg,
            aes(x = 4.5, y = 5.85, label = paste0(correct, "/", total)),
            inherit.aes = FALSE, family = "Arial", fontface = "bold",
            size = 2.25, colour = pal[["ink"]]) +
  facet_grid(model ~ obligation, switch = "y") +
  scale_fill_manual(values = c(`TRUE` = pal[["teal"]], `FALSE` = pal[["coral_light"]]),
                    guide = "none") +
  scale_x_continuous(limits = c(0.4, 8.6), expand = c(0, 0)) +
  scale_y_continuous(limits = c(0.4, 6.2), expand = c(0, 0)) +
  coord_cartesian(clip = "off") +
  labs(x = NULL, y = NULL, tag = "a") +
  theme_void(base_family = "Arial") +
  theme(
    plot.tag = element_text(family = "Arial", face = "bold", size = 9, colour = pal[["ink"]]),
    plot.tag.position = c(0, 1),
    strip.background = element_blank(),
    strip.placement = "outside",
    strip.text.x = element_text(family = "Arial", face = "bold", size = 6.8,
                                lineheight = 0.88, colour = pal[["slate"]]),
    strip.text.y.left = element_text(family = "Arial", size = 6.8,
                                     angle = 0, colour = pal[["ink"]]),
    panel.spacing.x = unit(3, "pt"), panel.spacing.y = unit(1.5, "pt"),
    plot.margin = margin(6, 3, 1, 4, "pt")
  )

case_df <- read.csv(file.path(source_dir, "fig4-v6-case-matrix.csv")) %>%
  mutate(
    model = factor(model, levels = rev(c("Mistral 14B", "LFM2 24B", "Llama MoE"))),
    obligation = if_else(case %in% c("direct_conflict", "gradual_conflict"),
                         "must quarantine", "must admit"),
    case = recode(case,
                  direct_conflict = "direct\nconflict",
                  gradual_conflict = "gradual\nconflict",
                  legitimate_state = "legitimate\nrevision",
                  unrelated = "unrelated\nsafe write"),
    case = factor(case, levels = c("direct\nconflict", "gradual\nconflict",
                                  "legitimate\nrevision", "unrelated\nsafe write")),
    obligation = factor(obligation, levels = c("must quarantine", "must admit"))
  )

p4b <- ggplot(case_df, aes(case, model, fill = accuracy)) +
  geom_tile(colour = "white", linewidth = 0.9) +
  geom_text(aes(label = percent(accuracy, accuracy = 1),
                colour = accuracy < 0.40 | accuracy >= 0.95),
            family = "Arial", fontface = "bold", size = 2.55) +
  facet_grid(. ~ obligation, scales = "free_x", space = "free_x") +
  scale_fill_gradient2(low = pal[["coral"]], mid = "#F4F1EC", high = pal[["teal"]],
                       midpoint = 0.5, limits = c(0, 1), guide = "none") +
  scale_colour_manual(values = c(`TRUE` = "white", `FALSE` = pal[["ink"]]), guide = "none") +
  labs(x = NULL, y = NULL, tag = "b") +
  theme_cmtw(7.2) +
  theme(
    axis.line = element_blank(), axis.ticks = element_blank(),
    axis.text.x = element_text(size = 6.3, lineheight = 0.86),
    axis.text.y = element_text(size = 6.8),
    strip.text = element_text(size = 6.5, face = "bold", colour = pal[["slate"]]),
    panel.spacing.x = unit(2.0, "pt"),
    plot.margin = margin(7, 4, 2, 4, "pt")
  )

fig4 <- p4a / p4b + plot_layout(heights = c(1.30, 0.88))
save_bundle(fig4, "cmtw-v11-fig4-admission-contract", 89, 82)

# -----------------------------------------------------------------------------
# Figure 5 - architecture first, then necessity and portability
# -----------------------------------------------------------------------------
# Panel a deliberately differs from Figure 2: it shows where lifecycle
# responsibilities meet, not how one object propagates through a trace.
lane5 <- tibble::tribble(
  ~y, ~input, ~op, ~responsibility, ~dark, ~light,
  39, "ASSERT",      "I", "persona admission",      pal[["teal"]],  pal[["teal_light"]],
  29, "AS-OF QUERY", "T", "valid-time eligibility", pal[["ochre"]], pal[["ochre_light"]],
  19, "FORGET",      "C", "recorded closure",       pal[["navy"]],  "#DCE5EC"
)
circle5 <- tibble::tibble(
  theta = seq(0, 2 * pi, length.out = 241),
  x = 105 + 16.5 * cos(theta),
  y = 29 + 16.5 * sin(theta)
)
hex5 <- tibble::tibble(
  x = c(92, 97, 114, 120, 114, 97),
  y = c(29, 37, 37, 29, 21, 21)
)
base5 <- tibble::tibble(
  x = c(65, 145, 136, 74),
  y = c(2, 2, 13, 13)
)
answer5 <- tibble::tibble(
  x = c(142, 171, 179, 171, 142),
  y = c(23, 23, 29, 35, 35)
)

p5a <- ggplot() +
  # A perspective substrate makes the core look supported, not appended.
  geom_polygon(data = base5, aes(x, y), fill = pal[["slate"]], colour = NA) +
  # Three low-saturation rails carry the lifecycle operations.
  geom_segment(data = lane5,
               aes(x = 9, xend = 73, y = y, yend = y, colour = light),
               linewidth = 4.0, lineend = "round") +
  geom_segment(data = lane5,
               aes(x = 9, xend = 73, y = y, yend = y, colour = dark),
               linewidth = 0.72, lineend = "round") +
  # AnswerTrace is an audit envelope around the evidence core.
  geom_polygon(data = circle5, aes(x, y), fill = pal[["teal_light"]],
               colour = pal[["teal"]], linewidth = 0.68) +
  geom_polygon(data = hex5, aes(x, y), fill = "white",
               colour = pal[["teal"]], linewidth = 0.80) +
  # Curved entries remain separate and terminate at the core boundary.
  annotate("curve", x = 72, y = 39, xend = 93, yend = 35,
           curvature = -0.13, colour = pal[["teal"]], linewidth = 0.72,
           arrow = arrow(length = unit(1.65, "mm"), type = "closed")) +
  annotate("segment", x = 72, y = 29, xend = 91.5, yend = 29,
           colour = pal[["ochre"]], linewidth = 0.72,
           arrow = arrow(length = unit(1.65, "mm"), type = "closed")) +
  annotate("curve", x = 72, y = 19, xend = 93, yend = 23,
           curvature = 0.13, colour = pal[["navy"]], linewidth = 0.72,
           arrow = arrow(length = unit(1.65, "mm"), type = "closed")) +
  # One short output connector; the arrow-shaped destination carries the action.
  annotate("segment", x = 121.7, y = 29, xend = 141.5, yend = 29,
           colour = pal[["teal"]], linewidth = 0.78,
           arrow = arrow(length = unit(1.65, "mm"), type = "closed")) +
  geom_polygon(data = answer5, aes(x, y), fill = pal[["teal_light"]],
               colour = pal[["teal"]], linewidth = 0.72) +
  # True-circle operator badges interrupt the rails without adding card clutter.
  annotate("point", x = 43, y = 39, shape = 21, size = 9.6,
           fill = pal[["teal"]], colour = pal[["teal"]], stroke = 0) +
  annotate("point", x = 43, y = 29, shape = 21, size = 9.6,
           fill = pal[["ochre"]], colour = pal[["ochre"]], stroke = 0) +
  annotate("point", x = 43, y = 19, shape = 21, size = 9.6,
           fill = pal[["navy"]], colour = pal[["navy"]], stroke = 0) +
  geom_text(data = lane5, aes(x = 43, y = y, label = op),
            family = "Arial", fontface = "bold", size = 2.65, colour = "white") +
  geom_text(data = lane5, aes(x = 9, y = y + 3.4, label = input),
            hjust = 0, family = "Arial", fontface = "bold", size = 2.20,
            colour = pal[["slate"]]) +
  geom_text(data = lane5, aes(x = 51, y = y + 3.4, label = responsibility),
            hjust = 0, family = "Arial", size = 2.05, colour = pal[["ink"]]) +
  # Open corner label avoids another enclosing rectangle.
  annotate("text", x = 7, y = 47.6, label = "CMTW CONTRACT PLANE",
           hjust = 0, family = "Arial", fontface = "bold", size = 2.55,
           colour = pal[["teal"]]) +
  annotate("segment", x = 7, xend = 69, y = 45.7, yend = 45.7,
           colour = pal[["teal"]], linewidth = 0.70) +
  # Core, audit, substrate, and output labels.
  annotate("text", x = 105, y = 42.3, label = "AnswerTrace",
           family = "Arial", fontface = "bold", size = 2.40,
           colour = pal[["teal"]]) +
  annotate("text", x = 105, y = 39.8, label = "replay  |  lineage  |  decision",
           family = "Arial", size = 1.78, colour = pal[["slate"]]) +
  annotate("text", x = 105.5, y = 30.7, label = "ELIGIBILITY-FIRST",
           family = "Arial", fontface = "bold", size = 2.25,
           colour = pal[["teal"]]) +
  annotate("text", x = 105.5, y = 27.2, label = "EVIDENCE CORE",
           family = "Arial", fontface = "bold", size = 2.25,
           colour = pal[["ink"]]) +
  annotate("text", x = 105, y = 8.2, label = "DATABASE SUBSTRATE",
           family = "Arial", fontface = "bold", size = 2.20, colour = "white") +
  annotate("text", x = 105, y = 4.9,
           label = "typed state  |  valid-time index  |  derivative ledger",
           family = "Arial", size = 1.78, colour = "white") +
  annotate("text", x = 158, y = 30.8, label = "ELIGIBLE",
           family = "Arial", fontface = "bold", size = 2.35,
           colour = pal[["teal"]]) +
  annotate("text", x = 158, y = 27.0, label = "ANSWER",
           family = "Arial", fontface = "bold", size = 2.35,
           colour = pal[["teal"]]) +
  scale_colour_identity() +
  scale_fill_identity() +
  coord_fixed(xlim = c(0, 183), ylim = c(0, 50), ratio = 1,
              expand = FALSE, clip = "off") +
  labs(tag = "a") +
  theme_void(base_family = "Arial") +
  theme(
    plot.tag = element_text(family = "Arial", face = "bold", size = 9,
                            colour = pal[["ink"]]),
    plot.tag.position = c(0, 1),
    plot.margin = margin(2, 3, 0, 3, "pt")
  )

config_levels <- c("I0 C0 T0", "I1 C0 T0", "I0 C1 T0", "I0 C0 T1",
                   "I1 C1 T0", "I1 C0 T1", "I0 C1 T1", "I1 C1 T1")
truth <- tidyr::expand_grid(I = 0:1, C = 0:1, T = 0:1) %>%
  mutate(config = paste0("I", I, " C", C, " T", T)) %>%
  transmute(config, persona = I, pollution = I, recorded_closure = C, valid_time = T) %>%
  pivot_longer(cols = c(persona, pollution, recorded_closure, valid_time),
               names_to = "operator", values_to = "present") %>%
  mutate(
    obligation = recode(operator,
                        persona = "persona",
                        pollution = "pollution",
                        recorded_closure = "recorded\nclosure",
                        valid_time = "valid-time\nselection"),
    config = factor(config, levels = rev(config_levels)),
    obligation = factor(obligation,
                        levels = c("persona", "pollution", "recorded\nclosure", "valid-time\nselection"))
  )

p5b <- ggplot(truth, aes(obligation, config, fill = factor(present))) +
  geom_tile(colour = "white", linewidth = 0.55) +
  geom_text(aes(label = if_else(present == 1, "PASS", "-"), colour = factor(present)),
            family = "Arial", fontface = "bold", size = 2.05) +
  scale_fill_manual(values = c(`0` = pal[["coral_light"]], `1` = pal[["teal_light"]])) +
  scale_colour_manual(values = c(`0` = pal[["coral"]], `1` = pal[["teal"]])) +
  scale_x_discrete(position = "top") +
  labs(x = NULL, y = NULL, tag = "b") +
  theme_cmtw(7.1) +
  theme(
    axis.line = element_blank(), axis.ticks = element_blank(),
    axis.text.x = element_text(size = 6.2, lineheight = 0.84, colour = pal[["slate"]]),
    axis.text.y = element_text(size = 6.1, colour = pal[["ink"]]),
    plot.margin = margin(7, 3, 2, 5, "pt")
  )

adh <- read.csv(file.path(source_dir, "fig5-v6-generator-adherence.csv")) %>%
  mutate(
    model = factor(model, levels = c("Mistral 14B", "LFM2 24B", "Llama MoE")),
    adherence_group = factor(sprintf("%.2f", adherence),
                             levels = c("0.50", "0.75", "1.00")),
    fill_group = recode(as.character(adherence_group),
                        `0.50` = pal[["coral"]],
                        `0.75` = pal[["ochre_mid"]],
                        `1.00` = pal[["teal"]])
  ) %>%
  group_by(model) %>%
  arrange(adherence, .by_group = TRUE) %>%
  mutate(cell = row_number(), cell_x = (cell - 1) %% 10 + 1,
         cell_y = 2 - floor((cell - 1) / 10)) %>%
  ungroup()
adh_summary <- adh %>% distinct(model, mean, bootstrap95_lo, bootstrap95_hi) %>%
  mutate(label = sprintf("mean %s\n95%% CI %s-%s",
                         percent(mean, accuracy = 0.1),
                         percent(bootstrap95_lo, accuracy = 0.1),
                         percent(bootstrap95_hi, accuracy = 0.1)))
key5 <- tibble::tibble(
  model = factor(rep("Mistral 14B", 3), levels = levels(adh$model)),
  xmin = c(1.0, 3.7, 6.4), xmax = c(1.6, 4.3, 7.0),
  xtext = c(1.8, 4.5, 7.2), label = c("50%", "75%", "100%"),
  fill = c(pal[["coral"]], pal[["ochre_mid"]], pal[["teal"]])
)

p5c <- ggplot(adh, aes(cell_x, cell_y)) +
  geom_tile(aes(fill = I(fill_group)), width = 0.82, height = 0.82,
            colour = "white", linewidth = 0.18) +
  geom_text(data = adh_summary, aes(x = 11.0, y = 1.5, label = label),
            inherit.aes = FALSE, hjust = 0, family = "Arial", size = 2.00,
            lineheight = 0.88, colour = pal[["ink"]]) +
  facet_grid(model ~ ., switch = "y") +
  geom_rect(data = key5,
            aes(xmin = xmin, xmax = xmax, ymin = 2.65, ymax = 2.95, fill = I(fill)),
            inherit.aes = FALSE, colour = NA) +
  geom_text(data = key5, aes(x = xtext, y = 2.80, label = label),
            inherit.aes = FALSE, hjust = 0, family = "Arial", size = 1.85,
            colour = pal[["slate"]]) +
  scale_x_continuous(limits = c(0.4, 15.0), expand = c(0, 0)) +
  scale_y_continuous(limits = c(0.4, 3.05), expand = c(0, 0)) +
  coord_fixed(ratio = 0.68) +
  labs(x = NULL, y = NULL, tag = "c") +
  theme_void(base_family = "Arial") +
  theme(
    plot.tag = element_text(family = "Arial", face = "bold", size = 9, colour = pal[["ink"]]),
    plot.tag.position = c(0, 1),
    strip.background = element_blank(), strip.placement = "outside",
    strip.text.y.left = element_text(family = "Arial", size = 6.8,
                                     angle = 0, colour = pal[["ink"]]),
    panel.spacing.y = unit(2, "pt"),
    plot.margin = margin(7, 5, 2, 4, "pt")
  )

bottom5 <- (p5b | p5c) + plot_layout(widths = c(0.44, 0.56))
fig5 <- (p5a / bottom5) + plot_layout(heights = c(1.25, 1.00))
save_bundle(fig5, "cmtw-v12-fig5-contract-architecture", 183, 84)

cat("Built CMTW v12 targeted figures from frozen source tables in", base_dir, "\n")
