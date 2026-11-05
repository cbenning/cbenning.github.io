# benninger.ca Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Jekyll site with a Zola site that has an original dark home-lab/workshop look (LED glow, blocky panels, pixel art), a projects page, and every existing post at its current URL.

**Architecture:** Zola 0.23.6 renders `content/` (posts, about, legacy project pages) through a hand-written theme in `templates/` and `sass/`. Project cards come from `data/projects.toml`. Pixel art is authored as text grids in `art/` and rendered to SVG in `static/art/` by a stdlib Python script. A stdlib `unittest` suite checks the built `public/` directory against a baseline captured from the live site. GitHub Actions builds, tests and deploys.

**Tech Stack:** Zola 0.23.6 (Tera templates, built-in Sass, giallo highlighting), Python 3 stdlib (tests, art tool), PyYAML for the one-off migration script only, GitHub Actions + Pages.

**Spec:** `docs/superpowers/specs/2026-11-05-site-redesign-design.md`

## Global Constraints

- Zola pinned to `v0.23.6`, Linux tarball `zola-v0.23.6-x86_64-unknown-linux-gnu.tar.gz`, sha256 `8f5132b3522412d04e395e0b25f6d68613ad272a873e54a2b3ebf664873024a4`. Same version locally and in CI.
- No Node, no npm, no CSS framework, no stock theme. Python tooling is stdlib only, except the migration script (Task 2), which may use PyYAML and is deleted in Task 7.
- Tokens, verbatim: `bg #0b0c0c`, `panel #151817`, `line #2b302e`, `text #d6dbd4`, `muted #7b847f`, `heading #f1f5ef`, `led #4dff91`, `led-glow rgba(77,255,145,.55)`, `amber #ffb000`, `red #ff4b3e`. Amber and red only as small status indicators.
- Glow only on lit things: status LEDs, active nav item, eyebrow labels, primary-button hover, LEDs in pixel art. Never on body text or headings in long-form content.
- Square corners, 2px borders, hard offset shadows with no blur (4 to 8px), hover/press transitions with `steps(2, end)`.
- Fonts self-hosted: Silkscreen 400 (headings, nav, buttons, labels) and JetBrains Mono 400/700 (body, code). No Google Fonts or other runtime font CDN.
- Analytics: GoatCounter only (`https://benninger.goatcounter.com/count`, script `//gc.zgo.at/count.js`). No Cloudflare beacon, no Disqus.
- Never publish the phone number `778-288-9371`. No CV page or CV nav item in this phase.
- Nav: HOME, PROJECTS, POSTS. Footer: GitHub `https://github.com/cbenning`, LinkedIn `https://www.linkedin.com/in/christopherbenninger`, email `chris@benninger.ca`, feed `/atom.xml`.
- No client JavaScript is required to read any page. The only `<script>` allowed on content pages is GoatCounter (Zola's generated redirect pages are exempt).
- Pixel art is original. Nothing copied from karamian.am, including its blue-black and amber palette.
- All work on branch `redesign`. Do not touch `master` or the repo's Pages settings until Task 8, and only with Chris's explicit go-ahead.

## Review Focus

1. WordPress `.html` posts parsed as markdown: indented lines turning into code blocks, `*`/`_` turning into emphasis, lost paragraphs. Expect the same words and the same number of code blocks as the live post. Test: `test_post_code_block_counts` (Task 2).
2. Feed readers: existing subscribers must not see all 40 posts again as new. Expect entry `<id>`s identical to today's. Test: `test_feed_ids_match_baseline` (Task 3).
3. Broken internal links and images (post screenshots, `/assets/*.tar.gz`, cross-links). Expect every root-relative `href`/`src` in built HTML to resolve to a file in `public/`. Test: `test_internal_links_resolve` (Task 6).
4. Phones at 360px: long code lines and wide tables (the Dune post) must scroll inside their box, not the page. Test: `test_css_overflow_rules` (Task 4).
5. Motion-sensitive and keyboard users: breathing LED and stepped transitions must stop under reduced motion, and focus must be visible. Test: `test_css_accessibility_rules` (Task 4).

---

## File Structure

```
config.toml                     Zola config
content/_index.md               home (template index.html)
content/about.md                /about/
content/articles.md             /articles/ (path = "articles", template archive.html)
content/posts/_index.md         posts section (redirect_to = "/articles/", page_template = "post.html")
content/posts/YYYY-MM-DD-*.md   43 migrated posts (3 with draft = true)
content/projects/_index.md      /projects/ (template projects.html)
content/projects/workviz.md     /projects/workviz/
content/projects/omega-editor-theme.md
data/projects.toml              project cards
templates/base.html             html shell, head, nav, footer, GoatCounter
templates/macros.html           led(), project_card(), post_list()
templates/index.html  post.html  page.html  archive.html  projects.html
templates/taxonomy_list.html  taxonomy_single.html  404.html
templates/atom.xml  feed.xml  llms.txt  llms-full.txt  robots.txt
sass/style.scss                 imports partials below
sass/_tokens.scss  _fonts.scss  _base.scss  _components.scss  _post.scss  _code.scss
static/fonts/                   woff2 files + OFL-silkscreen.txt + OFL-jetbrainsmono.txt
static/art/*.svg                generated pixel art (committed)
static/CNAME keybase.txt favicon.ico images/** assets/img/html5-{before,after}.png
static/assets/template.tar.gz  static/assets/omega_v0.1.tar.gz
art/*.txt                       pixel-art sources
scripts/install-zola.sh         downloads pinned Zola to .bin/zola, verifies sha256
scripts/test.sh                 install-zola, zola build, unittest
scripts/capture_baseline.py     one-off: live site -> tests/fixtures/
scripts/migrate_jekyll.py       one-off (deleted in Task 7)
scripts/pixelart.py             art/*.txt -> static/art/*.svg
tests/helpers.py                shared: PUBLIC dir, html_pages(), article_text(), load_fixture()
tests/fixtures/legacy-urls.txt  legacy-posts.json  legacy-feeds.json
tests/test_*.py
.github/workflows/deploy.yml
```

---

### Task 1: Toolchain, baseline capture, Zola skeleton

**Files:**
- Create: `scripts/install-zola.sh`, `scripts/test.sh`, `scripts/capture_baseline.py`, `config.toml`, `content/_index.md`, `templates/base.html`, `templates/index.html`, `tests/helpers.py`, `tests/test_build.py`, `tests/fixtures/legacy-urls.txt`, `tests/fixtures/legacy-posts.json`, `tests/fixtures/legacy-feeds.json`
- Modify: `.gitignore` (add `.bin/`, `public/`)

**Interfaces:**
- Produces: `scripts/test.sh` (exit 0 = build and all tests pass; it is the single entry point for local and CI runs).
- Produces in `tests/helpers.py`: `PUBLIC: pathlib.Path` (repo `public/`), `html_pages() -> list[Path]`, `article_text(html: str) -> str` (visible text inside the element with class `post-body`, whitespace-collapsed), `load_fixture(name: str)` (json or text from `tests/fixtures/`), `normalize(text: str) -> list[str]` (lowercased word list, punctuation stripped, HTML entities decoded).
- Produces fixtures:
  - `legacy-urls.txt`: one path per line, from `https://benninger.ca/sitemap.xml` plus `/llms.txt`, `/llms-full.txt`, `/keybase.txt`, `/favicon.ico`, every file under `images/`, and the four linked `assets/` files.
  - `legacy-posts.json`: `{slug: {"title": str, "words": [str], "code_blocks": int}}` for the 40 live posts, text from `div.entry-content`, `code_blocks` = count of `<pre>` in it.
  - `legacy-feeds.json`: `{"atom.xml": [ids], "feed.xml": [ids]}` in document order.

- [ ] **Step 1:** Write `scripts/install-zola.sh`: if `.bin/zola --version` prints `zola 0.23.6`, exit 0; else download the pinned tarball from `https://github.com/getzola/zola/releases/download/v0.23.6/`, verify the sha256 from Global Constraints (`sha256sum -c`), extract to `.bin/zola`. `set -euo pipefail`.
- [ ] **Step 2:** Write `scripts/test.sh`: run install-zola, `.bin/zola build`, `python3 -m unittest discover -s tests -v`. `set -euo pipefail`.
- [ ] **Step 3:** Write `scripts/capture_baseline.py` (stdlib `urllib`, `html.parser`) that fetches the live site and writes the three fixtures. Run it once: `python3 scripts/capture_baseline.py`. Expected: `legacy-posts.json` has exactly 40 keys; `legacy-feeds.json` has 40 atom ids (format `/posts/<slug>`) and 20 feed ids (format `https://benninger.ca/posts/<slug>`).
- [ ] **Step 4: Write failing test** `tests/test_build.py::test_home_exists`: `assert (PUBLIC / "index.html").is_file()`.
- [ ] **Step 5:** Run `scripts/test.sh`. Expected: FAIL (no Zola site yet).
- [ ] **Step 6:** Create `config.toml`: `base_url = "https://benninger.ca"`, `title = "Chris Benninger"`, `description = "Code, utilities and other projects"`, `generate_feeds = false` (Task 3 turns feeds on), `taxonomies = [{name = "tags"}]`, `[markdown.highlighting] style = "class"` with a built-in dark theme (restyled in Task 4). Minimal `content/_index.md`, `templates/base.html` (blocks `title`, `content`), `templates/index.html`.
- [ ] **Step 7:** Run `scripts/test.sh`. Expected: PASS.
- [ ] **Step 8: Commit** `git add -A scripts tests config.toml content templates .gitignore && git commit -m "Add Zola skeleton, toolchain and live-site baseline"`

### Task 2: Migrate posts, pages and static files

**Files:**
- Create: `scripts/migrate_jekyll.py`, `tests/test_migrate_jekyll.py`, `content/posts/_index.md`, `content/posts/*.md`, `content/about.md`, `content/articles.md`, `content/projects/_index.md`, `content/projects/workviz.md`, `content/projects/omega-editor-theme.md`, `templates/post.html`, `templates/page.html`, `templates/archive.html`, `templates/projects.html`, `templates/taxonomy_list.html`, `templates/taxonomy_single.html` (bare placeholders), `tests/test_posts.py`
- Move to `static/`: `CNAME`, `keybase.txt`, `favicon.ico`, `images/`, `assets/img/html5-before.png`, `assets/img/html5-after.png`, `assets/template.tar.gz`, `assets/omega_v0.1.tar.gz` (use `git mv`)

**Interfaces:**
- Consumes: `tests/helpers.py`, fixtures from Task 1.
- Produces in `scripts/migrate_jekyll.py`:
  - `convert_highlights(body: str) -> str`: every `{% highlight LANG %}...{% endhighlight %}` (also the malformed `{% highlight scala $}` and the one-line form) becomes a fenced block on its own lines: `\n```LANG\n<code>\n```\n`.
  - `strip_kramdown_ial(body: str) -> str`: removes lines that are only `{: ...}`.
  - `replace_site_url(body: str) -> str`: `{{ site.url }}` becomes `` (root-relative links).
  - `to_zola_front_matter(meta: dict, filename: str) -> str`: TOML block between `+++` lines with `title`, `date` (front-matter `date` if present, else filename date), `description` (if non-empty), `draft = true` when `published` is false, `[taxonomies] tags = [...]`, `[extra] categories = [...]`. Drops `layout`, `meta`, `status`, `type`, `comments`. Strings escaped with `json.dumps`.
  - `migrate_file(src: Path, dest_dir: Path) -> Path`: writes `dest_dir/<same stem>.md`.
  - `main()`: migrates `_posts/*`, `about.md`, `projects/workviz/index.html`, `projects/omega-editor-theme/index.html`.
- Produces in content: posts section has `redirect_to = "/articles/"`, `sort_by = "date"`, `page_template = "post.html"`. Every post body is rendered inside `<article class="post-body">` by `post.html`; pages by `page.html` use the same class.

- [ ] **Step 1: Write failing unit tests** in `tests/test_migrate_jekyll.py` (whole module `skipUnless` PyYAML importable):
  - `test_highlight_block`: `convert_highlights("a\n{% highlight bash %}\nls -l\n{% endhighlight %}\nb")` contains `"\n```bash\nls -l\n```\n"` and no `{%`.
  - `test_highlight_malformed_dollar`: `{% highlight scala $}x{% endhighlight %}` becomes a `scala` fence.
  - `test_highlight_one_line`: `{% highlight sh %}$ faad -o - in.m4a | lame - out.mp3{% endhighlight %}` becomes a `sh` fence containing that command.
  - `test_ial_removed`: `"|a|\n{: .styled-table}\nx"` becomes `"|a|\nx"`.
  - `test_site_url`: `'<img src="{{ site.url }}/assets/img/x.png">'` becomes `'<img src="/assets/img/x.png">'`.
  - `test_front_matter_draft`: meta `{"title": "T", "published": False, "tags": ["a"], "categories": ["c"], "layout": "post"}` with filename `2013-06-05-what-is-sphinux-os-.html` yields TOML containing `draft = true`, `date = 2013-06-05`, `tags = ["a"]`, and no `layout`.
  - `test_front_matter_quotes`: title `Scala: Declaring multiple vars as 'null' while "enforcing"` round-trips via `tomllib.loads`.
- [ ] **Step 2:** Run `python3 -m unittest tests.test_migrate_jekyll -v`. Expected: FAIL (module missing).
- [ ] **Step 3:** Implement `scripts/migrate_jekyll.py` with the interfaces above (PyYAML for reading Jekyll front matter).
- [ ] **Step 4:** Run the unit tests. Expected: PASS.
- [ ] **Step 5: Write failing site tests:**
  - `tests/test_posts.py::test_static_files`: `public/CNAME` reads `benninger.ca`; `public/keybase.txt`, `public/favicon.ico`, `public/images/posts/unison.png` and the four `assets/` files exist.
  - `tests/test_posts.py::test_post_text_matches_baseline`: for each slug in `legacy-posts.json`, `difflib.SequenceMatcher(None, baseline_words, normalize(article_text(new_html))).ratio() >= 0.97`; failure message names the slug and ratio.
  - `tests/test_posts.py::test_post_code_block_counts`: per slug, count of `<pre` inside the new `post-body` equals baseline `code_blocks`.
  - `tests/test_posts.py::test_drafts_not_built`: none of `scala-declaring-multiple-vars-as-null-and-enforcing-a-type`, `what-is-sphinux-os`, `what-is-sphinux-os-`, `jvm-more-than-just-java` exists under `public/posts/`.
  - `tests/test_posts.py::test_no_liquid_left`: no file in `content/` contains `{%` or `{{ site`.
- [ ] **Step 6:** Run `scripts/test.sh`. Expected: FAIL.
- [ ] **Step 7:** Run `python3 scripts/migrate_jekyll.py`, `git mv` the static files, add section/page `_index.md` files and bare templates that wrap content in `<article class="post-body">`.
- [ ] **Step 8:** Run `scripts/test.sh`. Expected: PASS. If a post fails the text ratio or code-block count, fix that post's markdown by hand (typical fixes: wrap a WordPress HTML fragment so markdown leaves it alone, escape a stray `*`), keeping the words unchanged.
- [ ] **Step 9: Commit** `git commit -m "Migrate Jekyll posts, pages and static files to Zola content"`

### Task 3: Feeds, sitemap, robots and llms files

**Files:**
- Create: `templates/atom.xml`, `templates/feed.xml`, `templates/llms.txt`, `templates/llms-full.txt`, `templates/robots.txt`, `tests/test_feeds.py`, `tests/test_urls.py`
- Modify: `config.toml` (`generate_feeds = true`, `feed_filenames = ["atom.xml", "feed.xml", "llms.txt", "llms-full.txt"]`)

**Interfaces:**
- Consumes: posts from Task 2, `legacy-feeds.json`.
- Produces: `/atom.xml` (all live posts, entry id `/posts/<slug>`), `/feed.xml` (latest 20, entry id `https://benninger.ca/posts/<slug>`), `/llms.txt`, `/llms-full.txt`, `/robots.txt`.

- [ ] **Step 1: Write failing tests** in `tests/test_feeds.py`:
  - `test_feeds_parse`: `atom.xml` and `feed.xml` parse with `xml.etree.ElementTree`; atom has 40 `entry` elements, feed has 20.
  - `test_feed_ids_match_baseline`: entry ids for each feed equal `legacy-feeds.json` exactly (same order).
  - `test_llms_txt`: `llms.txt` starts with `# Chris Benninger`, has 40 lines matching `^- \[.+\]\(https://benninger\.ca/posts/[^)]+/\)`, and links `https://benninger.ca/projects/` and `https://benninger.ca/about/` under `## Other`.
  - `test_llms_full`: `llms-full.txt` contains every baseline title and no `<p>` or `&amp;`.
  - `test_robots`: `robots.txt` equals `"User-agent: *\nAllow: /\n\nSitemap: https://benninger.ca/sitemap.xml\n"`.
  - `test_sitemap_has_posts`: `sitemap.xml` contains `https://benninger.ca/posts/<slug>/` for all 40 slugs and none of the draft slugs.
  - `tests/test_urls.py::test_legacy_urls_exist`: for each path in `legacy-urls.txt` not in `INTENTIONALLY_REMOVED`, `public/<path>` is a file or `public/<path>/index.html` exists. `INTENTIONALLY_REMOVED = {"/404/", "/projects/index2/", "/assets/css/main.css", "/assets/css/skins/dark.css", "/assets/css/skins/default.css", "/assets/css/skins/light.css", "/assets/js/search-data.js", "/js/highlight.js/", "/js/highlight.js/README.ru/"}`.
- [ ] **Step 2:** Run `scripts/test.sh`. Expected: FAIL.
- [ ] **Step 3:** Update `config.toml` and write the five templates. Feed templates iterate `pages` (Zola passes the same list to every feed filename); `feed.xml` uses `pages | slice(end=20)`. `llms.txt` and `llms-full.txt` follow the structure of today's Jekyll versions (see git history of `llms.txt`, `llms-full.txt`); `llms-full.txt` uses `striptags` then `replace` for `&lt; &gt; &quot; &#39; &amp;`, in that order.
- [ ] **Step 4:** Run `scripts/test.sh`. Expected: PASS.
- [ ] **Step 5: Commit** `git commit -m "Add Atom feeds, llms.txt files and robots.txt templates"`

### Task 4: Design system: fonts, tokens, base layout

**Files:**
- Create: `static/fonts/silkscreen-400.woff2`, `static/fonts/jetbrains-mono-400.woff2`, `static/fonts/jetbrains-mono-700.woff2`, `static/fonts/OFL-silkscreen.txt`, `static/fonts/OFL-jetbrainsmono.txt`, `sass/style.scss`, `sass/_tokens.scss`, `sass/_fonts.scss`, `sass/_base.scss`, `sass/_components.scss`, `sass/_post.scss`, `sass/_code.scss`, `templates/macros.html`, `templates/404.html`, `tests/test_design.py`
- Modify: `templates/base.html`, `config.toml` (`compile_sass = true`)

**Interfaces:**
- Produces CSS custom properties in `:root` (in `_tokens.scss`): `--bg --panel --line --text --muted --heading --led --led-glow --amber --red` with the Global Constraints values.
- Produces classes later tasks use: `.btn` `.btn--primary` `.btn--quiet`, `.panel` (2px border, hard shadow), `.eyebrow` (glowing LED-colour label), `.led` with modifiers `.led--active` (green), `.led--maintenance` and `.led--experimental` (amber), `.led--archived` (red, dimmed), `.led--breathe` (opacity pulse), `.chip` (tech tag), `.post-body` (long-form reading styles, measure 70 to 80ch, no glow).
- Produces in `templates/macros.html`: `led(status: str, label: bool = true, extra_class: str = "")` renders `<span class="led led--{status} {extra_class}" aria-hidden="true"></span>` plus a visible `<span class="led-label">{status}</span>` when `label`, else a `title` and `aria-label` on a wrapper so colour is never the only signal.
- Produces in `templates/base.html`: blocks `title`, `description`, `content`; nav items HOME `/`, PROJECTS `/projects/`, POSTS `/articles/` with `aria-current="page"` on the active one; footer links from Global Constraints; GoatCounter snippet; `<link rel="alternate" type="application/atom+xml" href="/atom.xml">`; canonical and Open Graph `og:title`, `og:description`, `og:url`; preload of the two 400-weight fonts.

- [ ] **Step 1:** Download fonts: `https://cdn.jsdelivr.net/fontsource/fonts/silkscreen@latest/latin-400-normal.woff2`, `.../jetbrains-mono@latest/latin-400-normal.woff2`, `.../jetbrains-mono@latest/latin-700-normal.woff2`; licences from `https://raw.githubusercontent.com/google/fonts/main/ofl/silkscreen/OFL.txt` and `.../ofl/jetbrainsmono/OFL.txt`.
- [ ] **Step 2: Write failing tests** in `tests/test_design.py`:
  - `test_contrast`: parse `--name: #rrggbb` from `sass/_tokens.scss`; WCAG contrast ratio ≥ 4.5 for `text`, `muted`, `heading`, `led` against both `bg` and `panel`.
  - `test_no_third_party`: no built HTML or CSS contains `fonts.googleapis`, `fonts.gstatic`, `cloudflareinsights`, `disqus`, or `778-288-9371`.
  - `test_goatcounter_everywhere`: every HTML page except Zola redirect pages (`<title>Redirect</title>`) contains `data-goatcounter="https://benninger.goatcounter.com/count"`, and its only `<script` tag is GoatCounter's.
  - `test_nav`: every non-redirect page has nav links to `/`, `/projects/`, `/articles/` and none to `/cv/`.
  - `test_css_overflow_rules`: compiled `public/style.css` has `overflow-x: auto` (or `overflow-x:auto`) in rules for `pre` and for `table`, and `img` has `max-width: 100%`.
  - `test_css_accessibility_rules`: compiled CSS has a `prefers-reduced-motion: reduce` block that sets `animation: none` and `transition: none`, and a `:focus-visible` rule.
  - `test_no_rounded_corners`: compiled CSS contains no `border-radius` with a non-zero value.
- [ ] **Step 3:** Run `scripts/test.sh`. Expected: FAIL.
- [ ] **Step 4:** Implement the Sass partials, `macros.html`, `base.html` and `404.html` (copy in the site's voice, for example heading `404: no route to host` and a link home). Restyle the giallo classes in `_code.scss` so code blocks sit on `--panel` with a 2px `--line` border.
- [ ] **Step 5:** Run `scripts/test.sh`. Expected: PASS.
- [ ] **Step 6:** Visual check: `.bin/zola serve`, open `http://127.0.0.1:1111/posts/fussel/` and `/posts/dune-awakening-server-proxmox/` at 1280px and 360px wide. Expected: readable, no page-level horizontal scroll, glow only on lit elements.
- [ ] **Step 7: Commit** `git commit -m "Add design system: tokens, fonts, base layout, 404"`

### Task 5: Pixel-art tool and artwork

**Files:**
- Create: `scripts/pixelart.py`, `tests/test_pixelart.py`, `art/hero-workbench.txt`, `art/davlog.txt`, `art/fussel.txt`, `art/ticktick-to-todoist-migrator.txt`, `static/art/*.svg` (generated)

**Interfaces:**
- Art file format: lines `C = #rrggbb` or `C = #rrggbb glow` (one char per colour), a blank line, then the grid; `.` is transparent; all grid rows equal length.
- Produces in `scripts/pixelart.py`:
  - `@dataclass Color(hex: str, glow: bool)`, `@dataclass Art(palette: dict[str, Color], rows: list[str])`
  - `parse_art(text: str) -> Art` raises `ValueError` naming the row number for ragged rows and naming the character for characters not in the palette.
  - `render_svg(art: Art, title: str) -> str`: `viewBox="0 0 W H"`, `shape-rendering="crispEdges"`, `role="img"`, `<title>`; one `<rect>` per horizontal run of the same colour; glow colours additionally drawn in a `<g filter="url(#glow)">` group using an `feGaussianBlur` filter defined only when a glow colour is used.
  - `main(argv: list[str]) -> int`: `python3 scripts/pixelart.py art static/art` renders every `art/*.txt` to `static/art/<stem>.svg`.
- Art content (palette drawn from the tokens plus neutral greys/wood/metal tones; never the reference site's blue-black and amber):
  - `hero-workbench`, 96×64: a workbench with a desk lamp casting a soft pool of light (warm tint allowed inside the art only), an open server chassis with a pulled drive or board, a screwdriver, a soldering iron, cables, and green glowing server LEDs.
  - `davlog`, 64×40: a filing cabinet or notebook with a git branch and a green LED.
  - `fussel`, 64×40: a wall or grid of framed photos.
  - `ticktick-to-todoist-migrator`, 64×40: a checklist moving from one box to another.

- [ ] **Step 1: Write failing tests** in `tests/test_pixelart.py`:
  - `test_run_merging`: palette `A`, `B`, grid `AAB` gives exactly 2 `<rect` in the output, the first with `width="2"`.
  - `test_ragged_rows`: rows `AA`, `A` raise `ValueError` whose message contains `row 2`.
  - `test_unknown_char`: grid `AZ` raises `ValueError` whose message contains `'Z'`.
  - `test_glow_only_when_used`: no `feGaussianBlur` without a glow colour; present with one.
  - `test_transparent`: `.` produces no rect.
  - `test_generated_files_current`: for each `art/*.txt`, `render_svg(parse_art(...), stem)` equals the committed `static/art/<stem>.svg`.
  - `test_art_sizes`: `hero-workbench` is 96×64; the three project pieces are 64×40.
- [ ] **Step 2:** Run `python3 -m unittest tests.test_pixelart -v`. Expected: FAIL.
- [ ] **Step 3:** Implement `scripts/pixelart.py`.
- [ ] **Step 4:** Draw the four art files, run `python3 scripts/pixelart.py art static/art`, and look at each SVG in a browser at 4× scale. Iterate until each one reads clearly as its subject.
- [ ] **Step 5:** Run `scripts/test.sh`. Expected: PASS.
- [ ] **Step 6: Commit** `git commit -m "Add pixel-art tool and original artwork"`

### Task 6: Home and projects pages

**Files:**
- Create: `data/projects.toml`, `tests/test_pages.py`
- Modify: `templates/index.html`, `templates/projects.html`, `templates/macros.html` (add `project_card`, `post_list`), `content/_index.md`, `content/projects/_index.md`

**Interfaces:**
- Consumes: `led()`, classes and tokens from Task 4; `/art/*.svg` from Task 5.
- `data/projects.toml` schema: `[[projects]]` with `id`, `name`, `pitch`, `description` (2 to 3 sentences from the repo README, no invented claims), `category`, `status` (`active|maintenance|experimental|archived`), `tech` (list), `repo`, optional `demo`, `post`, `stars` (int, typed by hand), `years`, `art` (path), `featured` (bool), `order` (int).
- Entries, in order:
  1. `davlog`: status `active`, category `self-hosting tool`, tech `["Rust", "WebDAV", "git"]`, repo `https://github.com/cbenning/davlog`, post `/posts/davlog/`, art `/art/davlog.svg`, pitch `A WebDAV server where every save is a git commit.`
  2. `fussel`: name `Fussel`, status `active`, category `photo gallery generator`, tech `["Python"]`, repo `https://github.com/cbenning/fussel`, demo `http://photos.benninger.ca`, post `/posts/fussel/`, stars `314`, art `/art/fussel.svg`, pitch `A static photo gallery generator with face-tag albums.`
  3. `ticktick-to-todoist-migrator`: status `active`, category `migration tool`, tech `["Python"]`, repo `https://github.com/cbenning/ticktick-to-todoist-migrator`, art `/art/ticktick-to-todoist-migrator.svg`, pitch `Migrate a TickTick CSV export into Todoist, with a preview run before anything is written.`
- Produces in `macros.html`: `project_card(p)` renders `<article class="project-card" id="{p.id}">` with art (`image-rendering: pixelated`), category eyebrow, name, pitch, description, `led(p.status)`, tech chips, and links (repo, demo, post when present); `post_list(pages)` renders date + title list items.
- Home copy (from the approved mockup): eyebrow `sys: online / victoria bc` with `led(status="active", label=false, extra_class="led--breathe")`; `<h1>Chris Benninger</h1>`; role `Software architect`; intro `Production systems by day. Home-lab experiments and side projects by night.`; buttons `SEE PROJECTS` → `/projects/` (primary) and `READ POSTS` → `/articles/` (quiet); hero art `/art/hero-workbench.svg`; then featured projects, then the latest 5 posts.

- [ ] **Step 1: Write failing tests** in `tests/test_pages.py`:
  - `test_projects_page_cards`: `/projects/index.html` has exactly 3 `class="project-card"`, ids `davlog`, `fussel`, `ticktick-to-todoist-migrator` in that order; each card contains a `led--active` element and the visible text `active`.
  - `test_project_links`: davlog card links `https://github.com/cbenning/davlog` and `/posts/davlog/`; fussel card links `http://photos.benninger.ca`.
  - `test_home`: `/index.html` contains `Chris Benninger`, `/art/hero-workbench.svg`, `led--breathe`, 3 project cards, and exactly 5 links to `/posts/…/` in the latest-posts list, the first being `/posts/davlog/`.
  - `test_internal_links_resolve`: for every built HTML page, every `href`/`src` starting with `/` (minus `#fragment` and `?query`) resolves to a file or a `…/index.html` under `public/`. Links already broken on today's live site may go in a `KNOWN_BROKEN` set in the test, each one confirmed 404 on `https://benninger.ca` with a comment saying so; nothing else may be exempted.
- [ ] **Step 2:** Run `scripts/test.sh`. Expected: FAIL.
- [ ] **Step 3:** Implement `data/projects.toml`, macros and the two templates (`projects.html` uses `load_data(path="data/projects.toml")` sorted by `order`; home shows entries with `featured = true`).
- [ ] **Step 4:** Run `scripts/test.sh`. Expected: PASS.
- [ ] **Step 5:** Visual check with `.bin/zola serve` at 1280px and 360px: cards stack on mobile, hover and press feel chunky, the breathing LED pulses.
- [ ] **Step 6: Commit** `git commit -m "Add home and projects pages"`

### Task 7: Post, archive, tags and about pages, CI workflow, Jekyll removal

**Files:**
- Modify: `templates/post.html`, `templates/page.html`, `templates/archive.html`, `templates/taxonomy_list.html`, `templates/taxonomy_single.html` (create if absent), `content/about.md`, `tests/test_pages.py`
- Create: `.github/workflows/deploy.yml`, `tests/test_repo.py`
- Delete: `_config.yml`, `Gemfile`, `Gemfile.lock`, `_layouts/`, `_includes/`, `_posts/`, `_assets/`, `_data/`, `.bundle/`, `vendor/`, `.jekyll-cache/`, `_site/`, `assets/` (after Task 2 moved the four kept files), `css/`, `js/`, `font/`, `script/`, `projects/`, `index.html`, `articles.html`, `tags.html`, `404.html`, `about.md`, `atom.xml`, `feed.xml`, `sitemap.xml`, `llms.txt`, `llms-full.txt`, `robots.txt`, `Makefile`, `Rakefile`, `readme.markdown`, `package.json`, `scripts/migrate_jekyll.py`, `tests/test_migrate_jekyll.py`

**Interfaces:**
- Consumes: everything above.
- Post page: title, date, tags (links to `/tags/<tag>/`), `post-body`, prev/next links. No comments.
- Archive `/articles/`: all live posts grouped by year, newest first, each with date and tags.
- About `/about/`: existing about text, restyled; keeps the Lego line.

- [ ] **Step 1: Write failing tests:**
  - `tests/test_pages.py::test_archive`: `/articles/index.html` lists 40 post links and year headings `2026` and `2010`, `2026` appearing first.
  - `tests/test_pages.py::test_post_page`: `/posts/davlog/index.html` has the post title in `<h1>`, a `<time datetime="2026-10-30`, and tag links under `/tags/`.
  - `tests/test_pages.py::test_tags_page`: `/tags/index.html` exists and links `/tags/linux/` (or Zola's slug for `Linux`).
  - `tests/test_repo.py::test_no_jekyll_files`: none of `_config.yml`, `Gemfile`, `_layouts`, `_includes`, `_posts` exists in the repo root.
  - `tests/test_repo.py::test_workflow_pins_zola`: `.github/workflows/deploy.yml` runs `scripts/test.sh` and uses `actions/upload-pages-artifact` and `actions/deploy-pages`.
- [ ] **Step 2:** Run `scripts/test.sh`. Expected: FAIL.
- [ ] **Step 3:** Implement the templates and restyle `about.md`.
- [ ] **Step 4:** Write `.github/workflows/deploy.yml`: triggers `push` to `master` and `workflow_dispatch`; `permissions: contents: read, pages: write, id-token: write`; `concurrency: group: pages`; job `build` on `ubuntu-latest`: `actions/checkout@v7`, `scripts/test.sh`, `actions/upload-pages-artifact@v5` with `path: public`; job `deploy` (needs build, environment `github-pages`): `actions/deploy-pages@v5`.
- [ ] **Step 5:** Delete the Jekyll files listed above with `git rm -r`.
- [ ] **Step 6:** Run `scripts/test.sh`. Expected: PASS, every test module green, no skipped tests (the migration tests are gone).
- [ ] **Step 7:** Lighthouse check (manual, uses the machine's Node and Chrome via `npx`, not a project dependency): `.bin/zola serve` then `npx lighthouse http://127.0.0.1:1111/<page> --only-categories=performance,accessibility --quiet` for `/`, `/projects/`, `/posts/dune-awakening-server-proxmox/`. Expected: both scores ≥ 95 on each. Fix and re-run if not.
- [ ] **Step 8: Commit** `git commit -m "Add post, archive and tag pages, deploy workflow; remove Jekyll"`

### Task 8: Cutover (requires Chris's explicit go-ahead)

**STOP before this task.** Show Chris the finished branch (summary plus `.bin/zola serve` preview) and ask for approval to go live. Do nothing below without it.

- [ ] **Step 1:** Push the branch: `git push -u origin redesign`.
- [ ] **Step 2:** Switch Pages to Actions: `gh api -X PUT repos/cbenning/cbenning.github.io/pages -f build_type=workflow`. Expected: `gh api repos/cbenning/cbenning.github.io/pages --jq .build_type` prints `workflow`; the current site stays served until the next deployment.
- [ ] **Step 3:** Merge to `master` (fast-forward or PR, as Chris prefers) and push.
- [ ] **Step 4:** Watch the run: `gh run watch` on the `deploy.yml` run. Expected: success.
- [ ] **Step 5:** Verify live: run `tests/test_urls.py` logic against `https://benninger.ca` (fetch each fixture URL, expect HTTP 200), check `https://benninger.ca/atom.xml` ids match the fixture, and confirm HTTPS and the custom domain still work (`gh api repos/cbenning/cbenning.github.io/pages --jq .cname` prints `benninger.ca`).
- [ ] **Step 6:** Rollback if anything is broken: `gh api -X PUT repos/cbenning/cbenning.github.io/pages -f build_type=legacy -f "source[branch]=master" -f "source[path]=/"` and revert the merge commit on `master`.
