# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Chris Benninger's personal site (benninger.ca), built with [Zola](https://www.getzola.org/) (a Rust static site generator, pinned to **0.23.6**). It was migrated from Jekyll in November 2026; the design and migration are recorded in `docs/superpowers/specs/2026-11-05-site-redesign-design.md` and `docs/superpowers/plans/2026-11-05-site-redesign.md` — read those for the *why* behind the structure below before making structural changes.

Dark "home-lab/workshop" theme: blocky panels, hard offset shadows, a single LED-green accent for status/interactive elements, original pixel art, self-hosted pixel + mono fonts. No client JavaScript except GoatCounter analytics.

## Commands

```bash
bash scripts/test.sh          # the one command: installs pinned Zola, builds the site, runs all tests
python3 -m unittest tests.test_pages -v                    # one test module (run from tests/, or discover -s tests)
python3 -m unittest tests.test_pages.TestHomePage.test_home -v   # one test
.bin/zola serve                                             # local dev server with live reload (localhost:1111)
python3 scripts/pixelart.py art static/art                  # regenerate all pixel-art SVGs after editing art/*.txt
```

`scripts/test.sh` is the single entry point locally and in CI (`.github/workflows/deploy.yml`) — it downloads/verifies Zola via sha256 into `.bin/`, runs `zola build`, then `python3 -m unittest discover -s tests`. Always run it (not just `zola build`) before considering a change done: most behavioral guarantees (URL compatibility, feed format, accessibility, no third-party scripts) are enforced by the test suite reading the built `public/` output, not by the build succeeding.

There is no npm/node toolchain. Fonts and the `lighthouse` CLI used during development were invoked via `npx` as one-off tools, not project dependencies.

## Architecture

### Tera has no `{% macro %}` or `{% import %}`

This Zola/Tera build (confirmed empirically, see `templates/macros.html` header comment) does not support macros — not a missing-dependency issue, a real engine limitation. Reusable UI fragments are built as **dispatch-on-variable includes** instead:

- `templates/macros.html` — set a `partial` variable (`"project_card"` or `"post_list"`) plus that partial's own variables, then `{% include "macros.html" %}`.
- `templates/_led.html` — the status-LED partial lives in its *own* file because Tera also rejects a template including itself, even with different variables each call (so `macros.html`'s `project_card` branch can't `{% include "macros.html" %}` again for its LED).

When adding a new reusable fragment, follow this same pattern and document the variable contract in a comment at the top of the file, as the existing ones do.

### Content model

- `content/posts/*.md` — 40 blog posts, migrated from Jekyll with permalinks preserved (`/posts/:slug/`). `content/posts/_index.md` has `redirect_to = "/articles/"` — the section itself redirects, `templates/archive.html` (serving `content/articles.md`) is the real post index.
- `content/projects/` — `workviz.md` and `omega-editor-theme.md` are legacy standalone pages kept at their old URLs; the *current* project list (davlog, Lanby, Fussel, ticktick-to-todoist-migrator) is **not** content — it's data.
- `data/projects.toml` — the project cards shown on `/` (featured only) and `/projects/` (all, sorted by `order`). Schema: `id, name, pitch, description, category, status, tech[], art, art_width, art_height, featured, order`, plus any of `repo, site, docs, demo, post, stars` (links render only for fields that are present — see `templates/macros.html`'s `project_card` branch). `status` drives the LED colour: `active` (green, breathing), `maintenance`/`experimental` (amber), `archived` (red, dimmed).
- `data/tech-colors.toml` — language/tool → hex colour for the dot on each tech chip, keyed by **lowercased** label; unknown keys fall back to a neutral grey. Add entries here, not in CSS, when a new project uses a new technology.

### Pixel art pipeline

`art/*.txt` (hand-authored text grids: a palette header, then rows of characters, `.` = transparent) → `scripts/pixelart.py art static/art` → `static/art/*.svg`. The SVGs are committed; `tests/test_pixelart.py::test_generated_files_current` fails the build if a `.txt` source and its `.svg` have drifted apart, so always regenerate after editing an art source. Art files are authored as small Python scripts using `scripts/pixelart.py`'s `Grid` helper during design (see commit history for examples) and then hand-tuned; there is no separate "art builder" committed to the repo.

### Design tokens and CSS

`sass/_tokens.scss` defines the palette as CSS custom properties (`--bg`, `--panel`, `--text`, `--led`, `--led-ink` for prose links, `--amber`, `--red`, etc.) — change colors there, not by hardcoding hex in component files. Each `sass/_*.scss` partial owns one concern (`_base`, `_components`, `_home`, `_post`, `_code`, `_fonts`) and is imported by `style.scss`; Zola compiles Sass itself (`compile_sass = true` in `config.toml`), no separate build step.

Fonts are self-hosted in `static/fonts/` (Jersey 15 for pixel/display text, JetBrains Mono for body/code) with their OFL licenses alongside — never add a Google Fonts or other third-party font link; `tests/test_design.py::test_no_third_party` enforces no third-party script/font origins and no Disqus.

The syntax-highlighting theme (`giallo`, configured in `config.toml`) generates `public/giallo.css`; `sass/_code.scss` overrides specific token classes (e.g. `.z-3` for comments) where the generated theme's contrast fails WCAG against `--panel`.

### Baseline/migration tests

`tests/fixtures/legacy-*.json` are snapshots of the *live* pre-migration Jekyll site (posts' text and code-block counts, feed entry ids/timestamps), captured by `scripts/capture_baseline.py`. Several tests (`test_posts.py`, `test_feeds.py`) diff the new Zola output against these fixtures rather than asserting fixed expected values — this is intentional, to guarantee the rewrite didn't silently change post content or break existing feed subscribers. Don't delete or "simplify" these fixtures; if a legitimate content change makes a comparison fail, update the fixture deliberately and explain why in the commit.

### What must never appear in output

Enforced by `tests/test_design.py::test_no_third_party` and related tests: no Google Fonts, no Cloudflare Insights, no Disqus, no email address, no phone number, GoatCounter as the *only* script tag on every page. If you add any third-party embed, you'll need to update that test deliberately, not route around it.

## Deployment

`.github/workflows/deploy.yml` runs `scripts/test.sh` then deploys `public/` via `actions/upload-pages-artifact` + `actions/deploy-pages` to GitHub Pages, triggered on push to `master`. The repo's GitHub Pages source must be set to "GitHub Actions" (not the legacy Jekyll build) for this to take effect — if `master` is still on the legacy Jekyll Pages build, merging this branch will not deploy correctly until that setting is switched.
