# Frontend verification, 25 October 2026

Direction selected by the owner: sports performance editorial, ivory, charcoal, burnt orange, strong typography. Anti Slop applied during implementation. ENERGY 2 / RHYTHM 2 / MOTION 1. Decision reasons are in [DESIGN.md](../DESIGN.md).

## Delivery gate

### Hard gate

- R-02 PASS: no em dashes or template marketing claims in the authored UI.
- R-03 PASS: browser measurements at 320, 390, 600, 768, 1024 and 1440px showed document scroll width equal to its available width. Tables scroll within their own regions.
- R-17 PASS: history summaries derive from `data.js`; tables use exported metrics; simulator outputs are identified as illustrative.
- R-18 PASS: no testimonials, fictional people or profile images.
- R-23 PASS: text product name; existing destinations, source data and body illustration retained. No new image assets or logos.
- R-24 PASS: the three navigation links update the URL to existing simulator, timeline and benchmark section IDs.
- R-25 PASS: 15 computed text/background pairs meet 4.5:1. Lowest verified pair is accent on the highlighted row, 4.73:1. Input rails meet 3.11:1 and daily chart bars meet 4.24:1.
- R-26 PASS: four presets, eight sliders, reset, athlete selector, three CSV downloads, two disclosures and camera reset exercised in the browser; outcomes recorded below.
- R-27 PASS: initial loading copy is in HTML. Automated cases verify missing exports, empty exports and a missing chart library. Data download remains available when chart rendering is unavailable.
- R-28 PASS: no FAQ added.
- R-32 PASS: eight sliders adjusted using ArrowRight; both disclosures opened with Enter; focused slider had a visible solid outline. Semantic buttons, labels, navigation and skip link are present.
- R-33 PASS: implementation edited in the source files; Prettier used only for formatting.
- R-34 PASS: one owner-selected light theme. No unfinished theme toggle.
- R-35 PASS: served with Python HTTP server and exercised in the in-app browser; console error/warning list empty. `node --check app.js` and five frontend tests pass.
- R-36 PASS: no invented claims. Removed athlete-clearance language and identified formula outputs separately from actual trained-model metrics.
- R-37 PASS: owner selected the editorial direction before the frontend source was changed; direction and dials documented.
- R-38 PASS: real exported histories and metrics, explicitly illustrative scenario outputs; no synthetic roster, feed or customer content.

### Purpose gate

- R-01 PASS: burnt orange anchors editorial hierarchy and upward contributions; colors follow the selected direction. No ornamental gradients.
- R-04 PASS: no decorative icon library or emoji. Advisory symbols indicate the computed scenario state.
- R-06 PASS: condensed sports editorial headings and open body typography, with their reasons recorded.
- R-07 PASS: no background grid; the former decorative 3D floor grid was removed.
- R-08 PASS: arrows identify source links or downloadable files, not every action.
- R-09 PASS: compact labels represent actual computed scenario state; no marketing badges.
- R-10 PASS: no backdrop blur or glass panels.
- R-12 PASS: no floating card shadows. Slider thumb outline separates the control from its rail.
- R-13 PASS: no interface glow or pulsing status indicators.
- R-14 PASS: no feature-card grid. Inputs, response, timeline and evidence have distinct content-driven structures.
- R-19 PASS: no automatic body rotation or chart animation. Reduced-motion preference disables smooth scrolling; 3D render loop pauses when its disclosure is closed.
- R-22 PASS: existing conceptual body view retained behind a disclosure and described as an illustration, not an injury localization.

### Liveliness

- PASS: dials stated in DESIGN.md and consistent with the static, typographic editorial layout.
- PASS: title is the introductory focal point; response values lead the experiment; chart leads the history; comparison table leads the research.
- PASS: section rules, condensed type and restrained orange repeat as identity motifs.
- PASS: whitespace separates research contexts, while controls remain close to their labels and results.

### Craftsmanship and quality locks

- C-1 / R-31 PASS: palette, typography, layout, spacing, surfaces, illustration and motion each have a written reason in DESIGN.md.
- C-2 PASS: recorded browser controls have actual behaviors; no placeholder action buttons.
- C-3 / R-05 PASS: only the existing research workflows remain; no pricing, testimonials, feature grid or filler activity.
- C-4 PASS: responsive reflow, keyboard-operated controls and explicit data failure states checked. Third-party libraries remain network dependencies with failure messages.
- C-5 PASS: tables derive from the real export rather than duplicated presentation numbers.
- R-11 PASS: restrained 2–3px surface radii; round slider thumbs denote draggable handles, not a universal pill treatment.
- R-15 / R-16 PASS: specific controls such as Reset inputs and Download athlete CSV; no generic marketing CTAs or AI superlatives.
- R-20 / R-30 PASS: sports editorial type and workload-specific composition; no popular-product clone.
- R-21 / R-29 PASS: fixed light palette reflects owner choice; charcoal and ivory ground the page, orange is the editorial accent, green and warm caution tones identify states.

## Recorded browser interactions

| Control                | Observed result                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------- |
| Recovered              | 0.5% illustrative risk, 9.3 readiness; selected state updated                               |
| Workload spike         | 23.5% illustrative risk, 3.8 readiness                                                      |
| High strain            | 76.9% illustrative risk, 1.0 readiness                                                      |
| Sleep deficit          | 24.0% illustrative risk, 1.0 readiness                                                      |
| All eight sliders      | ArrowRight updates linked output; preset clears and label becomes Custom scenario           |
| Reset inputs           | Recovered values and selected state restored                                                |
| 3D disclosure          | One WebGL canvas created, no loading error; keyboard Enter also opens and closes            |
| Reset view             | Camera reset handler executes; no console errors                                            |
| Statistical disclosure | Opens exported five-row comparison; keyboard Enter closes it                                |
| Four athlete options   | All update summary: 731 records each; 45, 0, 46 and 4 reported injury days respectively     |
| Athlete CSV            | Browser saved TeamB-4405bb1f-daily-records.csv                                              |
| Model CSV              | Browser saved model_comparison.csv                                                          |
| Statistics CSV         | Browser saved statistical_tests.csv                                                         |
| Main navigation        | URL updates to each real section anchor                                                     |
| Source link            | Click invoked on the verified repository URL; external links retain normal new-tab behavior |
| Home/brand             | Returns to the top content anchor                                                           |

External dataset and methodology URLs retain their original verified repository/DOI destinations. Browser runtime produced no warnings or errors during the checked interactions.

## Automated checks

Run `node --test tests/frontend.test.cjs` (no npm installation needed):

1. Presets update outputs without a browser-global `event`.
2. Missing data reports actionable errors while the simulator remains usable.
3. Empty exports report empty states and disable unavailable athlete actions.
4. Missing Chart.js preserves record summaries and CSV access.
5. Model table uses actual exported test metrics, sorted by PR-AUC, and statistics use exported records.

Also checked JavaScript syntax, whitespace errors and computed WCAG contrast ratios. No Python model or data-pipeline code changed; training was not rerun. Real-device mobile keyboard behavior and assistive-technology speech were not tested.
