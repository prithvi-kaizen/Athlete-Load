# AthleteLoad Design System & Visual Architecture

An elite sports-science design system inspired by high-performance telemetry platforms (Catapult Sports, Whoop, Apple Fitness+, Linear).

---

## 1. Design Philosophy

- **Data-Dense Yet Legible**: Professional coaches and performance directors need immediate signal without cognitive friction.
- **Biomechanical Authenticity**: Visuals (colors, charts, 3D anatomical heatmaps) reflect real human physiology and load dynamics.
- **Explainability First**: Every predictive metric is visually connected to its causal sports-science drivers through TreeSHAP attributions.
- **Non-Generic Aesthetics**: Avoids generic template gradients and cookie-cutter cards. Uses tactile glassmorphism, pitch-inspired color tones, and bespoke typography.

---

## 2. Color System & Design Tokens

### Core Palette
| Token | Hex / RGBA | Usage |
| :--- | :--- | :--- |
| `--bg-pitch` | `#06090e` | Deep pitch background |
| `--bg-card` | `rgba(13, 19, 33, 0.75)` | Frosted glass card surface |
| `--bg-card-elevated` | `rgba(20, 28, 48, 0.90)` | Active panels and interactive cards |
| `--border-subtle` | `rgba(255, 255, 255, 0.08)` | Structural dividers and card borders |
| `--border-focus` | `rgba(59, 130, 246, 0.5)` | Active input and focus states |

### Biomechanical Semantic Tokens
| Token | Hex | Meaning / Physical State |
| :--- | :--- | :--- |
| `--color-optimal` | `#10b981` | Optimal recovery, ACWR in sweet spot (0.8 - 1.3) |
| `--color-warning` | `#f59e0b` | Moderate surge, elevated fatigue (ACWR 1.3 - 1.5) |
| `--color-strain` | `#ef4444` | Danger zone, severe acute overload (ACWR > 1.5) |
| `--color-telemetry` | `#06b6d4` | Live session metrics and questionnaire logs |
| `--color-brand` | `#3b82f6` | Primary actions and navigational anchors |

---

## 3. Typography Hierarchy

- **Display & Numerical Values**: `Outfit` (800 / 700 / 600 weight) for big risk percentages, ACWR badges, and section headings.
- **User Interface & Body Text**: `Plus Jakarta Sans` (400 / 500 / 600 weight) for crisp legibility and technical descriptions.
- **Telemetry & Statistical Data**: `JetBrains Mono` / Tabular Numerals for date stamps, $p$-values, effect sizes, and SHAP delta values.

---

## 4. 3D Biomechanical Visualization (Img2ThreeJS)

- **Anatomical Wireframe Mesh**: A 3D human athletic silhouette with interactive anatomical joint nodes.
- **Dynamic Risk Heatmap**: Real-time vertex and material shader transitions reflecting slider inputs:
  - **Hamstrings & Groin**: Reflects Acute Training Load surges and Muscle Soreness Z-Scores.
  - **Knees & Ankles**: Reflects ACWR ratios and Cumulative 7-day volume.
  - **Core & Upper Body**: Reflects Fatigue and Sleep Debt.
- **Orbital Interaction**: 360-degree rotation, pitch angle control, and responsive rendering on all display resolutions.

---

## 5. Component Anatomy

1. **Telemetry Sliders**: Custom track with glowing dynamic thumbs, real-time value tags, and subtext explaining the sports-science metric.
2. **Dynamic TreeSHAP Waterfall**: Bi-directional bar chart with exact positive ($+$) and negative ($-$) log-odds contributions and animated width transitions.
3. **Dual-Axis Timeline Explorer**: Interactive Chart.js timeline showing session volume, acute/chronic workload curves, and red scatter markers for injury reports.
4. **Coaching Advisory Box**: Adaptive alert card with dynamic contextual guidance for training session modification.
