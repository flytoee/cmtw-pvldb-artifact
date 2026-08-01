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

theme_cmtw <- function(base_size = 7.2) {
  theme_classic(base_size = base_size, base_family = "Arial") +
    theme(
      axis.line = element_line(linewidth = 0.34, colour = pal[["ink"]]),
      axis.ticks = element_line(linewidth = 0.34, colour = pal[["ink"]]),
      axis.text = element_text(colour = pal[["ink"]]),
      axis.title = element_text(colour = pal[["ink"]]),
      legend.position = "none",
      panel.grid = element_blank(),
      plot.margin = margin(3, 3, 3, 3, "pt"),
      plot.tag = element_text(family = "Arial", face = "bold", size = 9,
                              colour = pal[["ink"]]),
      plot.tag.position = c(0, 1),
      strip.background = element_blank(),
      strip.text = element_text(face = "bold", colour = pal[["slate"]], size = 6.5)
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

model_cols <- c(
  "Mistral 14B" = unname(pal[["teal"]]),
  "LFM2 24B" = unname(pal[["ochre"]]),
  "Llama MoE" = unname(pal[["navy"]])
)

# -----------------------------------------------------------------------------
# Figure 4: admission failure -> failure localization -> contract necessity.
# Rebuilt directly from frozen CSV tables; no web/HTML drawing source is used.
# -----------------------------------------------------------------------------
if (FALSE) {
adm_seed <- read.csv(file.path(source_dir, "fig4-v6-admission-seeds.csv")) %>%
  mutate(model = factor(model, levels = c("Mistral 14B", "LFM2 24B", "Llama MoE"))) %>%
  group_by(model, safe_admission, contamination_recall) %>%
  arrange(seed, .by_group = TRUE) %>%
  mutate(
    local_n = n(),
    local_i = row_number(),
    offset = if_else(local_n == 1, 0, seq(-0.018, 0.018, length.out = first(local_n))),
    safe_plot = safe_admission + offset,
    recall_plot = contamination_recall + rev(offset)
  ) %>%
  ungroup()

frontier <- read.csv(file.path(source_dir, "fig4-admission-frontier.csv")) %>%
  mutate(
    model = recode(model, `Llama 3.2 MoE` = "Llama MoE"),
    model = factor(model, levels = c("Mistral 14B", "LFM2 24B", "Llama MoE")),
    safe = 1 - fq,
    safe_lo = 1 - fq_hi,
    safe_hi = 1 - fq_lo
  )

label_a <- tibble::tribble(
  ~model, ~x, ~y, ~hjust,
  "Mistral 14B", 0.67, 0.89, 0,
  "LFM2 24B", 0.02, 0.80, 0,
  "Llama MoE", 0.72, 0.11, 0
) %>% mutate(model = factor(model, levels = levels(frontier$model)))

p4a <- ggplot() +
  annotate("rect", xmin = 0.95, xmax = 1.055, ymin = 0.95, ymax = 1.055,
           fill = pal[["teal_light"]], colour = NA) +
  geom_point(data = adm_seed,
             aes(safe_plot, recall_plot, colour = model),
             size = 1.35, alpha = 0.78) +
  geom_segment(data = frontier,
               aes(x = safe_lo, xend = safe_hi, y = recall, yend = recall,
                   colour = model), linewidth = 0.50) +
  geom_segment(data = frontier,
               aes(x = safe_lo, xend = safe_lo, y = recall - 0.026,
                   yend = recall + 0.026, colour = model), linewidth = 0.50) +
  geom_segment(data = frontier,
               aes(x = safe_hi, xend = safe_hi, y = recall - 0.026,
                   yend = recall + 0.026, colour = model), linewidth = 0.50) +
  geom_point(data = frontier,
             aes(safe, recall, fill = model),
             shape = 23, size = 3.8, colour = pal[["ink"]], stroke = 0.55) +
  geom_text(data = label_a,
            aes(x, y, label = model, colour = model, hjust = hjust),
            family = "Arial", fontface = "bold", size = 2.25) +
  annotate("text", x = 0.910, y = 1.050, label = "target ≥.95 / .95",
           hjust = 1, vjust = 0.5, family = "Arial", fontface = "bold",
           size = 1.75, colour = pal[["teal"]]) +
  scale_colour_manual(values = model_cols) +
  scale_fill_manual(values = model_cols) +
  scale_x_continuous(limits = c(-0.065, 1.065), breaks = c(0, 0.5, 1.0),
                     labels = c("0", ".5", "1"), expand = c(0, 0)) +
  scale_y_continuous(limits = c(-0.065, 1.065), breaks = c(0, 0.5, 1.0),
                     labels = c("0", ".5", "1"), expand = c(0, 0)) +
  coord_cartesian(clip = "off") +
  labs(x = "safe-write admission", y = "contamination recall", tag = "a") +
  theme_cmtw(7.0) +
  theme(
    axis.title = element_text(size = 6.6),
    axis.text = element_text(size = 6.2),
    plot.margin = margin(7, 4, 2, 5, "pt")
  )

case_err <- read.csv(file.path(source_dir, "fig4-v6-case-matrix.csv")) %>%
  mutate(
    errors = round(n * (1 - accuracy)),
    error_rate = errors / n,
    label = sprintf("%d/%d", errors, n),
    model = factor(model, levels = rev(c("Mistral 14B", "LFM2 24B", "Llama MoE"))),
    obligation = if_else(case %in% c("direct_conflict", "gradual_conflict"),
                         "must quarantine", "must admit"),
    case = recode(case,
                  direct_conflict = "direct\nconflict",
                  gradual_conflict = "gradual\nconflict",
                  legitimate_state = "valid\nrevision",
                  unrelated = "safe\nwrite"),
    case = factor(case, levels = c("direct\nconflict", "gradual\nconflict",
                                  "valid\nrevision", "safe\nwrite")),
    obligation = factor(obligation, levels = c("must quarantine", "must admit"))
  )

p4b <- ggplot(case_err, aes(case, model, fill = error_rate)) +
  geom_tile(colour = "white", linewidth = 0.90) +
  geom_text(aes(label = label, colour = error_rate >= 0.48),
            family = "Arial", fontface = "bold", size = 2.35) +
  facet_grid(. ~ obligation, scales = "free_x", space = "free_x") +
  scale_fill_gradient(low = pal[["neutral_light"]], high = pal[["coral"]],
                      limits = c(0, 1), guide = "none") +
  scale_colour_manual(values = c(`FALSE` = pal[["slate_mid"]], `TRUE` = "white"),
                      guide = "none") +
  scale_x_discrete(position = "top") +
  labs(x = NULL, y = NULL, tag = "b") +
  theme_cmtw(7.0) +
  theme(
    axis.line = element_blank(), axis.ticks = element_blank(),
    axis.text.x = element_text(size = 5.8, lineheight = 0.85, colour = pal[["slate"]]),
    axis.text.y = element_text(size = 6.3),
    strip.text = element_text(size = 6.1, face = "bold", colour = pal[["ink"]]),
    panel.spacing.x = unit(2.4, "pt"),
    plot.margin = margin(7, 4, 2, 4, "pt")
  )

config_levels <- c("000", "001", "010", "011", "100", "101", "110", "111")
truth <- expand_grid(I = 0:1, C = 0:1, T = 0:1) %>%
  mutate(config = paste0(I, C, T)) %>%
  transmute(config,
            `Persona integrity` = I,
            `Pollution rejection` = I,
            `Recorded closure` = C,
            `As-of eligibility` = T) %>%
  pivot_longer(-config, names_to = "obligation", values_to = "present") %>%
  mutate(
    config = factor(config, levels = config_levels),
    obligation = factor(obligation,
      levels = rev(c("Persona integrity", "Pollution rejection",
                     "Recorded closure", "As-of eligibility"))),
    mark = if_else(present == 1, "1", "")
  )

p4c <- ggplot(truth, aes(config, obligation, fill = factor(present))) +
  geom_tile(colour = "white", linewidth = 0.70, width = 0.93, height = 0.84) +
  geom_text(aes(label = mark, colour = factor(present)), family = "Arial",
            fontface = "bold", size = 2.55) +
  annotate("rect", xmin = 7.52, xmax = 8.48, ymin = 0.56, ymax = 4.44,
           fill = NA, colour = pal[["teal"]], linewidth = 0.85) +
  annotate("text", x = 8.63, y = 4.22, label = "complete",
           hjust = 0, family = "Arial", fontface = "bold", size = 2.05,
           colour = pal[["teal"]]) +
  scale_fill_manual(values = c(`0` = pal[["coral_light"]], `1` = pal[["teal"]])) +
  scale_colour_manual(values = c(`0` = pal[["coral_mid"]], `1` = "white"),
                      guide = "none") +
  scale_x_discrete(position = "top", expand = expansion(add = c(0.10, 0.72))) +
  scale_y_discrete(expand = expansion(add = 0.08)) +
  coord_cartesian(clip = "off") +
  labs(x = "I / C / T configuration", y = NULL, tag = "c") +
  theme_cmtw(7.1) +
  theme(
    axis.line = element_blank(), axis.ticks = element_blank(),
    axis.text.x = element_text(size = 6.1, colour = pal[["ink"]]),
    axis.text.y = element_text(size = 6.2, colour = pal[["ink"]]),
    axis.title.x = element_text(size = 6.2, colour = pal[["slate"]], margin = margin(t = 2)),
    plot.margin = margin(4, 19, 1, 5, "pt")
  )

fig4_top <- p4a | p4b + plot_layout(widths = c(1.07, 0.93))
fig4 <- fig4_top / p4c + plot_layout(heights = c(1.16, 0.76))
save_bundle(fig4, "cmtw-v14-fig4-lifecycle-correctness", 183, 68)
}

# -----------------------------------------------------------------------------
# Figure 5: contract architecture -> generator-dependent answer boundary.
# -----------------------------------------------------------------------------
lane5 <- tibble::tribble(
  ~y, ~input, ~input_x, ~op, ~responsibility, ~dark, ~light,
  70, "Assertion",       8.0, "I", "admission", pal[["teal"]],  pal[["teal_light"]],
  48, "Forget",          8.0, "C", "cascade", pal[["ochre"]], pal[["ochre_light"]],
  26, "As-of query",     3.5, "T", "valid-time", pal[["navy"]],  "#DCE5EC"
)
route5 <- bind_rows(lapply(seq_len(nrow(lane5)), function(i) {
  z <- lane5[i, ]
  if (z$op == "I") {
    pts <- tibble(x = c(8, 60, 66.8), y = c(70, 70, 56.5))
  } else if (z$op == "C") {
    pts <- tibble(x = c(8, 63.8), y = c(48, 48))
  } else {
    pts <- tibble(x = c(8, 60, 66.8), y = c(26, 26, 39.5))
  }
  pts %>% mutate(route = i, dark = z$dark, light = z$light)
}))
circle5 <- tibble(
  theta = seq(0, 2 * pi, length.out = 241),
  x = 82 + 20.5 * cos(theta),
  y = 48 + 20.5 * sin(theta)
)
hex5 <- tibble(
  x = c(64, 70, 94, 100, 94, 70),
  y = c(48, 59, 59, 48, 37, 37)
)
base5 <- tibble(
  x = c(45, 119, 109, 55),
  y = c(1.0, 1.0, 17.5, 17.5)
)
answer5 <- tibble(
  x = c(108, 130, 139, 130, 108),
  y = c(41, 41, 48, 55, 55)
)

p5a <- ggplot() +
  geom_polygon(data = base5, aes(x, y), fill = pal[["slate"]], colour = NA) +
  geom_path(data = route5,
            aes(x = x, y = y, group = route, colour = light),
            linewidth = 5.0, lineend = "round", linejoin = "round") +
  geom_polygon(data = circle5, aes(x, y), fill = pal[["teal_light"]],
               colour = pal[["teal"]], linewidth = 0.67) +
  geom_polygon(data = hex5, aes(x, y), fill = "white",
               colour = pal[["teal"]], linewidth = 0.77) +
  geom_path(data = route5,
            aes(x = x, y = y, group = route, colour = dark),
            linewidth = 0.84, lineend = "round", linejoin = "round",
            arrow = arrow(length = unit(1.85, "mm"), type = "closed")) +
  annotate("segment", x = 82, xend = 82, y = 17.2, yend = 28.2,
           colour = pal[["slate_mid"]], linewidth = 0.70,
           arrow = arrow(length = unit(1.75, "mm"), type = "closed")) +
  annotate("segment", x = 102.5, y = 48, xend = 107.5, yend = 48,
           colour = pal[["teal"]], linewidth = 0.82,
           arrow = arrow(length = unit(1.85, "mm"), type = "closed")) +
  geom_polygon(data = answer5, aes(x, y), fill = pal[["teal_light"]],
               colour = pal[["teal"]], linewidth = 0.68) +
  annotate("point", x = 35, y = 70, shape = 21, size = 12.0,
           fill = pal[["teal"]], colour = pal[["teal"]], stroke = 0) +
  annotate("point", x = 35, y = 48, shape = 21, size = 12.0,
           fill = pal[["ochre"]], colour = pal[["ochre"]], stroke = 0) +
  annotate("point", x = 35, y = 26, shape = 21, size = 12.0,
           fill = pal[["navy"]], colour = pal[["navy"]], stroke = 0) +
  geom_text(data = lane5, aes(x = 35, y = y, label = op),
             family = "Arial", fontface = "bold", size = 3.35, colour = "white") +
  geom_text(data = lane5, aes(x = input_x, y = y + 5.3, label = input),
             hjust = 0, family = "Arial", fontface = "bold", size = 2.42,
            colour = pal[["slate"]]) +
  geom_text(data = lane5,
            aes(x = 46.5, y = c(63.0, 53.0, 31.0), label = responsibility),
            hjust = 0, family = "Arial", size = 1.88,
            colour = pal[["slate"]]) +
  annotate("text", x = 84, y = 79.4, label = "AnswerTrace",
           family = "Arial", fontface = "bold", size = 2.85,
           colour = pal[["teal"]]) +
  annotate("text", x = 84, y = 75.7,
           label = "selected IDs  |  eligibility  |  lineage",
           family = "Arial", size = 2.02, colour = pal[["slate"]]) +
  annotate("text", x = 82, y = 61.5, label = "Eligibility-first",
           family = "Arial", fontface = "bold", size = 2.20,
           colour = pal[["teal"]]) +
  annotate("text", x = 82, y = 50.0, label = "Evidence",
           family = "Arial", fontface = "bold", size = 2.66,
           colour = pal[["ink"]]) +
  annotate("text", x = 82, y = 45.5, label = "core",
           family = "Arial", fontface = "bold", size = 2.66,
           colour = pal[["ink"]]) +
  annotate("text", x = 82, y = 11.8, label = "Database substrate",
           family = "Arial", fontface = "bold", size = 2.38, colour = "white") +
  annotate("text", x = 82, y = 6.2,
            label = "typed state  |  valid-time index  |  derivation registry",
           family = "Arial", size = 1.72, colour = "white") +
  annotate("text", x = 123, y = 50.2, label = "Eligible",
           family = "Arial", fontface = "bold", size = 2.65,
           colour = pal[["teal"]]) +
  annotate("text", x = 123, y = 45.8, label = "answer",
           family = "Arial", fontface = "bold", size = 2.65,
           colour = pal[["teal"]]) +
  scale_colour_identity() +
  scale_fill_identity() +
  coord_fixed(xlim = c(0, 145), ylim = c(0, 86), ratio = 1,
              expand = FALSE, clip = "off") +
  labs(tag = "a") +
  theme_void(base_family = "Arial") +
  theme(
    plot.tag = element_text(family = "Arial", face = "bold", size = 9,
                            colour = pal[["ink"]]),
    plot.tag.position = c(0, 1),
    plot.margin = margin(2, 3, 2, 3, "pt")
  )

adh <- read.csv(file.path(source_dir, "fig5-v6-generator-adherence.csv")) %>%
  mutate(
    model = factor(model, levels = c("Mistral 14B", "LFM2 24B", "Llama MoE")),
    code = recode(as.character(model),
                  `Mistral 14B` = "MI", `LFM2 24B` = "LF", `Llama MoE` = "LL"),
    base_y = recode(as.character(model),
                    `Mistral 14B` = 74, `LFM2 24B` = 46,
                    `Llama MoE` = 18)
  )

adh_summary <- adh %>%
  distinct(model, mean, bootstrap95_lo, bootstrap95_hi) %>%
  mutate(mean = as.numeric(mean),
         bootstrap95_lo = as.numeric(bootstrap95_lo),
         bootstrap95_hi = as.numeric(bootstrap95_hi),
         base_y = recode(as.character(model),
                          `Mistral 14B` = 74, `LFM2 24B` = 46,
                          `Llama MoE` = 18),
         code = recode(as.character(model),
                       `Mistral 14B` = "MI", `LFM2 24B` = "LF", `Llama MoE` = "LL"),
         colour = case_when(
           mean >= 0.90 ~ pal[["teal"]],
           mean >= 0.65 ~ pal[["ochre"]],
           TRUE ~ pal[["coral"]]
         ),
         label = sprintf("%s  [%s, %s]",
                         percent(mean, accuracy = 0.1),
                         percent(bootstrap95_lo, accuracy = 0.1),
                         percent(bootstrap95_hi, accuracy = 0.1)),
         display_lo = ifelse(bootstrap95_lo == bootstrap95_hi,
                             mean - 0.018, bootstrap95_lo),
         display_hi = ifelse(bootstrap95_lo == bootstrap95_hi,
                             mean + 0.018, bootstrap95_hi),
         label_hjust = ifelse(mean >= 0.95, 1, 0.5))

adh_support <- adh %>%
  count(model, code, adherence, name = "n") %>%
  arrange(model, adherence) %>%
  group_by(model, code) %>%
  summarise(support = paste0(n, " at ", percent(as.numeric(adherence), accuracy = 1),
                             collapse = "  |  "), .groups = "drop") %>%
  left_join(adh_summary %>% select(model, mean, label_hjust), by = "model") %>%
  mutate(base_y = recode(as.character(model),
                         `Mistral 14B` = 74, `LFM2 24B` = 46,
                         `Llama MoE` = 18))

lantern5 <- bind_rows(lapply(seq_len(nrow(adh_summary)), function(i) {
  z <- adh_summary[i, ]
  half_h <- 6.2
  shoulder <- min(0.018, (z$display_hi - z$display_lo) / 3)
  tibble(
    model = z$model,
    x = c(z$display_lo,
          z$display_lo + shoulder,
          z$display_hi - shoulder,
          z$display_hi,
          z$display_hi - shoulder,
          z$display_lo + shoulder),
    y = c(z$base_y,
          z$base_y + half_h,
          z$base_y + half_h,
          z$base_y,
          z$base_y - half_h,
          z$base_y - half_h),
    colour = z$colour
  )
}))

p5b <- ggplot() +
  geom_segment(data = adh_summary,
               aes(x = display_lo, xend = display_hi,
                   y = base_y, yend = base_y, colour = I(colour)),
               linewidth = 7.0, lineend = "round", alpha = 0.20) +
  geom_polygon(data = lantern5,
               aes(x = x, y = y, group = model,
                   fill = I(colour), colour = I(colour)),
               alpha = 0.27, linewidth = 0.66) +
  geom_segment(data = adh_summary,
               aes(x = mean, xend = mean,
                   y = base_y - 6.2, yend = base_y + 6.2),
               colour = "white", linewidth = 0.78) +
  geom_text(data = adh_summary,
            aes(x = 0.485, y = base_y, label = code),
            hjust = 1, family = "Arial", size = 2.65,
            fontface = "bold", colour = pal[["ink"]]) +
  geom_text(data = adh_summary,
            aes(x = mean, y = base_y + 9.1, label = label,
                hjust = label_hjust, colour = I(colour)),
            family = "Arial", size = 1.96, fontface = "bold") +
  geom_text(data = adh_support,
            aes(x = mean, y = base_y - 9.2, label = support,
                hjust = label_hjust),
            family = "Arial", size = 1.78, colour = pal[["slate"]]) +
  annotate("text", x = 0.745, y = 95,
           label = "mean and bootstrap 95% CI",
           family = "Arial", size = 1.92, colour = pal[["slate"]]) +
  scale_x_continuous(limits = c(0.45, 1.045),
                     breaks = c(0.50, 0.75, 1.00),
                     labels = c("50%", "75%", "100%"),
                     expand = c(0, 0)) +
  scale_y_continuous(limits = c(0, 100), expand = c(0, 0)) +
  coord_cartesian(xlim = c(0.45, 1.045), ylim = c(0, 100), expand = FALSE,
                  clip = "off") +
  labs(x = "answer adherence across 20 seeds", y = NULL, tag = "b") +
  theme_classic(base_family = "Arial") +
  theme(
    axis.line.y = element_blank(),
    axis.ticks.y = element_blank(),
    axis.text.y = element_blank(),
    axis.line.x = element_line(linewidth = 0.34, colour = pal[["ink"]]),
    axis.ticks.x = element_line(linewidth = 0.34, colour = pal[["ink"]]),
    axis.text.x = element_text(family = "Arial", size = 6.4,
                               colour = pal[["slate"]]),
    axis.title.x = element_text(family = "Arial", size = 6.1,
                                colour = pal[["slate"]], margin = margin(t = 2)),
    plot.tag = element_text(family = "Arial", face = "bold", size = 9,
                            colour = pal[["ink"]]),
    plot.tag.position = c(0, 1),
    plot.margin = margin(2, 6, 5, 6, "pt")
  )

fig5 <- (p5a | p5b) + plot_layout(widths = c(113, 70))
save_bundle(fig5, "cmtw-v27-fig5-contract-portability", 183, 68)

contract_text <- c(
  "CMTW v27 figure contract",
  "========================",
  "Fig. 4 core conclusion: prompt-only identity admission has no usable operating point, and full lifecycle correctness requires I, C, and T.",
  "Fig. 4 panel map: (a) enlarged admission operating plane; (b) semantic error matrix; (c) full-width exact I/C/T obligation audit.",
  "Fig. 5 core conclusion: CMTW binds admission, valid-time eligibility, and recorded closure into an auditable database contract while downstream answer adherence remains generator-dependent.",
  "Fig. 5 panel map: (a) contract-plane architecture; (b) nonredundant confidence-lantern view of 20-seed generator adherence under one complete evidence surface.",
  "Archetypes: Fig. 4 quantitative grid; Fig. 5 asymmetric schematic-led composite.",
  "Backend: R only (ggplot2 + patchwork).",
  "Output: 183-mm vector PDF/SVG plus 600-dpi TIFF and review PNG.",
  "Integrity: all marks are generated from frozen CSV source tables; no HTML drawing code is used.",
  "Layout-only revision from v26: the As-of query label is shifted left to clear the T operator node; data and encodings are unchanged.",
  "Reviewer risk: Fig. 4c is a deterministic completeness audit, not an interaction or population estimate; Fig. 5b exposes rather than removes generator dependence."
)
writeLines(contract_text, file.path(base_dir, "figure-contract-v27.txt"), useBytes = TRUE)

cat("Built CMTW v27 Fig. 5 from frozen source tables in", base_dir, "\n")
