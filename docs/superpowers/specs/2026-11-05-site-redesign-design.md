# benninger.ca redesign: design

Date: 2026-11-05
Owner: Chris Benninger
Status: awaiting final approval

## 1. Intent

benninger.ca is Chris's personal site: a blog going back to 2010, a place to show off side projects, and the home for his CV. Today it runs a stock Jekyll theme that looks dated and generic, the projects page is hidden and stuck in 2019, and there is no CV at all.

Chris wants the site to look like it belongs to someone who builds things: a dark, techie, nerdy look with a home-lab, workshop and hacking feel. The signature detail is a gentle LED glow, like a status light on a piece of hardware in a dark room. Pixel art carries the personality.

The redesign should make it easy for a visitor to see who Chris is and what he has built (davlog, Fussel and others). The blog stays, intact. The site will also host his CV, but that is follow-up work (section 7).

## 2. Goals, non-goals, anti-goals

Goals:
- A new, original visual identity (section 4) applied to every page.
- A real Projects page that highlights davlog, Fussel and other projects as rich cards.
- Keep every existing post readable at its current URL.
- Keep everything that already works outside the theme: custom domain, analytics, feeds, sitemap, llms.txt files, robots.txt, keybase.txt.
- A simpler, modern build than the current Jekyll setup, with local and production builds matching.

Non-goals:
- Rewriting or editing old post content (beyond mechanical conversion needed to build).
- Multi-language support.
- A CMS, search, or a newsletter.
- Comments (see section 9, decision D6).
- The CV page (deferred to follow-up work, section 7).

Anti-goals (failure even if it technically works):
- Anything that looks copied from https://karamian.am/, the site Chris used as a reference. That site only conveys the sense of what he likes: blocky feel, monospace type, pixel art, dark colours. Specifically, do not use its deep blue-black background with amber accents, its exact layout, copy, icons or art.
- A generic "hacker" theme: green-on-black Matrix text, glitch effects, everything glowing.
- Glow on body text, or anything that makes long posts tiring to read.
- Broken old links.
- A heavy JavaScript bundle for what is a static content site.

## 3. Current state (facts as of 2026-11-05)

- Generator: Jekyll. GitHub Pages builds it with its legacy builder (Jekyll 3.10) from `master`; the local build uses Jekyll 4.4. Theme: `remote_theme: mmistakes/so-simple-theme`, but local `_layouts/` and `_includes/` from an older Bootstrap theme ("UP") override most of it.
- Dead leftovers from that older theme: `Makefile`, `Rakefile`, `readme.markdown`, `_assets/` (less, bootstrap js), most of `assets/`, `css/up.css`, `js/`, `font/`, `script/`, `package.json`. Exception: four files in `assets/` are still linked and must keep their URLs: `/assets/img/html5-before.png`, `/assets/img/html5-after.png` (2015 post), `/assets/template.tar.gz` (2010 Emulab switches post), `/assets/omega_v0.1.tar.gz` (Omega editor theme page).
- Posts: 43 files in `_posts/`, 2010 to 2026: 38 `.html` (WordPress import) and 5 `.md`. Three have `published: false` (`2012-10-24-scala-declaring-multiple-vars-as-null-and-enforcing-a-type`, `2013-06-05-what-is-sphinux-os-`, `2013-06-12-jvm-more-than-just-java`), so 40 are live (matching the 40 folders in `_site/posts/`). Liquid inside posts: 71 `{% highlight %}...{% endhighlight %}` blocks, plus two `{{ site.url }}` uses in `2015-12-08-debian-jessie-firefox-html5.html`. 40 posts have `comments: true` (Disqus, `disqus_shortname: benningerca`). Permalinks: `/posts/:title/`.
- Pages: `index.html` (latest 10 posts), `about.md` (`/about/`), `articles.html` (`/articles/`), `tags.html` (`/tags/`), `projects.md` (`/projects/`, nav link commented out in `_config.yml`), `projects/workviz/index.html`, `projects/omega-editor-theme/index.html`, `projects/index2.html`, `404.html`.
- Feeds: both `feed.xml` and `atom.xml` exist (Atom, Liquid-generated). `sitemap.xml` is hand-templated.
- Analytics: `_includes/analytics.html` loads Cloudflare Web Analytics and GoatCounter (`benninger.goatcounter.com`).
- LLM access: `robots.txt`, `llms.txt`, `llms-full.txt` (Liquid-generated from posts).
- Other root files to keep: `CNAME` (`benninger.ca`), `keybase.txt`, `favicon.ico`, `LICENSE`, `images/` (profile photos, post screenshots in `images/posts/`).
- CV source: private repo `cbenning/resume`, `resume.md` (Oh My CV markdown format, with HTML spans and iconify icons) plus `Chris_Benninger.pdf`. Last updated 2024-08-10. It contains a phone number.

## 4. Visual design

Decided with Chris through mockups (direction "home-lab rack", palette "Graphite + phosphor green"). The mockups are in `.superpowers/brainstorm/` for reference; they are throwaway, not code to reuse.

### 4.1 Mood

Home lab, workshop, hacking: a server rack, a workbench, a soldering iron, cables, a terminal. Hardware in a dark room, with small lights on. Not a retro CRT and not a Matrix screen.

### 4.2 Palette (decided)

| Token | Value | Use |
|---|---|---|
| `bg` | `#0b0c0c` | page background; neutral grey-black, no blue tint |
| `panel` | `#151817` | cards, code blocks, raised surfaces |
| `line` | `#2b302e` | borders, hard shadows on light-coloured elements |
| `text` | `#d6dbd4` | body text |
| `muted` | `#7b847f` | dates, captions, inactive nav |
| `heading` | `#f1f5ef` | headings |
| `led` | `#4dff91` | main LED colour: primary buttons, active nav, eyebrow labels, status light, links (builder may soften links if contrast or glare demands) |
| `led-glow` | `rgba(77,255,145,.55)` | glow colour for lit elements |
| `amber` | `#ffb000` | status only |
| `red` | `#ff4b3e` | status only |

Amber and red appear only as small status indicators, never as large fills or as the main accent. Syntax-highlighting colours for code blocks are the builder's call but must sit within this palette's mood.

### 4.3 Glow (decided)

"Warm glow" means the gentle bloom of an LED on a dark background. Apply glow only to things that are "lit": status LEDs, the active nav item, small eyebrow labels, primary-button hover, LEDs inside pixel art. Never on body text or headings in long-form content. The status light may slowly "breathe" (opacity pulse); all animation stops under `prefers-reduced-motion: reduce`.

### 4.4 Blocky feel and type (decided)

- Square corners everywhere. 2px borders. Hard offset shadows with no blur (about 4 to 8px).
- Hover and press effects move in steps (for example `steps(2, end)`), so buttons feel chunky: hover lifts the element and grows its shadow, press pushes it into its shadow.
- Fonts: a pixel font for headings, nav, buttons and labels (Silkscreen was used in mockups); a monospace font for body text and code (JetBrains Mono in mockups). Both are OFL-licensed. Self-host them; do not load Google Fonts at runtime. Builder may choose different pixel or mono faces if they read better, as long as the look holds. Body text must stay comfortable for long posts (size, line height, measure about 70 to 80 characters).
- Pixel images use `image-rendering: pixelated`.

### 4.5 Status LED language (my call, Chris to confirm while reading)

Small LEDs carry meaning on project cards:
- green, steady: active
- amber: maintenance only, or experimental
- red, dim: archived

Each LED has a text label or tooltip so colour is never the only signal.

### 4.6 Pixel art

Original art only. Home-lab, workshop and hacking themes.

Planned pieces:
- Hero (decided): a workbench scene with a desk lamp and a disassembled server on it. My call on details: open server chassis with a pulled drive or board, a few tools (screwdriver, soldering iron), cables, the lamp casting a soft pool of light, and the server's status LEDs glowing green. The lamp's light may be a soft warm tint inside the artwork only; UI colours stay as in 4.2.
- One scene per featured project, for example: davlog as a filing cabinet or notebook with a git branch; Fussel as a wall of photos; the IDA Pro plugins as a disassembly terminal; Workviz as a 3D wireframe of servers.
- Small icons (about 32px) for section headings.

Chris decided the builder makes the art to start: hand-built pixel art (SVG built from pixel grids, as in the mockups, or PNG), original, in the palette. Keep a clean way to swap any piece for a PNG or WebP later, in case Chris replaces some art. LEDs inside sprites may glow.

## 5. Site structure

| Page | URL | Content |
|---|---|---|
| Home | `/` | Hero (name, one-line role, short intro, status LED, workbench art), featured projects (3 to 4 cards linking to `/projects/`), latest posts (about 5), contact links |
| Projects | `/projects/` | All project cards (section 6) |
| Posts | `/articles/` | Full archive, grouped by year, with tags |
| Post | `/posts/:title/` | Unchanged URLs |
| Tags | `/tags/` | Tag index (keep the URL) |
| About | `/about/` | Keep the URL. My call: short about text, can be merged into the home hero, with `/about/` kept as a real page so the link does not break |
| 404 | `/404.html` | Restyled, in the site's voice (for example "no route to host") |

Navigation: Home, Projects, Posts (CV added in the follow-up). Footer: GitHub, LinkedIn, email, feed.

Existing project subpages `/projects/workviz/` and `/projects/omega-editor-theme/` must keep working (the Workviz GitHub repo links to the first). They can be restyled or become simple pages; `/projects/index2.html` can go.

## 6. Projects page

Each project is an entry with these fields (stored as described in 8.1), rendered as a blocky card with a pixel-art scene:
- name, one-line pitch, longer description (a few sentences)
- category label (for example "self-hosting tool")
- status (active / maintenance / archived) shown as an LED
- tech tags (language, key libraries)
- links: repo, demo or homepage, related blog post
- optional: GitHub stars, years active
- art: image or placeholder sprite id
- featured flag and sort order

Initial list (decided by Chris): start with these three, all featured. More projects get added later as new entries, no template changes.

- **davlog** (Rust, active): WebDAV server where every save is a git commit. Related post: `/posts/davlog/`.
- **Fussel** (Python, active, 314 stars): static photo gallery generator with face-tag albums. Demo: photos.benninger.ca. Related post: the 2020 Fussel post.
- **ticktick-to-todoist-migrator** (Python, active): migrates a TickTick CSV export into Todoist with a preview run.

Candidates for later (not in this phase): the IDA Pro plugins (idapro_dataflow etc.), Maitland, xen_shm, Workviz, Omega editor theme, nhl-score-bot. Workviz and Omega keep their existing pages at their current URLs regardless.

Data entry for projects is manual (no build-time GitHub API calls), so builds stay offline and reproducible. Star counts, if shown, are typed in by hand.

## 7. CV page (deferred to follow-up work)

Chris decided the CV is follow-up work, not part of this redesign. Do not build a `/cv/` page or a CV nav item in this phase. Notes for the follow-up, so they are not lost:
- Source: `resume.md` in the private `cbenning/resume` repo (Oh My CV markdown with HTML spans and iconify icons), last updated 2024-08. Chris will decide whether to refresh it first.
- Never publish the phone number. The existing `Chris_Benninger.pdf` contains it, so it cannot be linked as-is.
- Intended shape: summary, experience as a blocky timeline with tech-tag chips, then other sections; print stylesheet in light colours.
- The design should leave room for a fourth nav item (CV) so adding it later needs no redesign.

## 8. Technology and build

### 8.1 Generator: Zola (decided by Chris)

Zola, a single Rust binary. Reasons: nothing to install or update besides one binary (no Node, no npm, low supply-chain exposure), built-in Sass, syntax highlighting, taxonomies, Atom feeds and sitemap, Tera templates (close to Liquid), and date-prefixed filenames map to slugs the same way Jekyll's `:title` does. The site has no interactive needs, so a JavaScript framework buys nothing. Alternatives considered and rejected: Astro (Node toolchain churn), Hugo (awkward Go templates), Eleventy, staying on Jekyll.

Use a custom theme built from scratch in the site's own `templates/` and `sass/`; do not start from a stock Zola theme. No CSS framework; plain Sass/CSS with custom properties for the tokens in 4.2. Pin the Zola version (same version locally and in CI).

Projects are data, not posts: keep them in a TOML data file (or one page per project in a `projects` section, builder's choice) with the fields listed in section 6.

`llms.txt` and `llms-full.txt` are not normal pages. Zola may be able to emit them through feed templates (`feed_filenames`); this is unverified. If it cannot, generate them with a small script step in the build workflow. Either way they must be produced from the post content on every build, not hand-maintained.

### 8.2 Content migration

- Move all 43 posts (40 live, 3 unpublished) into a Zola `posts` section, preserving `title`, date, `tags`, `categories`, `description` and slug so URLs stay `/posts/:title/`. The slug is derived from the Jekyll filename (date prefix removed), same as Jekyll's `:title`. Zola slugifies filenames, which can change some slugs (for example a trailing dash); set an explicit `slug` (or adjust slugify settings) wherever the result would differ from the current URL. Builder must verify every old URL still resolves (compare against the current `_site/posts/` listing).
- Convert `{% highlight lang %}...{% endhighlight %}` blocks to fenced code blocks with a script, not by hand. Replace the two `{{ site.url }}` uses in the 2015 Firefox post with root-relative URLs.
- The 38 `.html` posts: convert to markdown files whose body stays as raw HTML (markdown passes HTML through), or render them through an HTML-capable path. Builder's choice; content must look right in the new styles.
- Drop WordPress leftovers in frontmatter (`meta`, `_edit_last`, `status`, `type`) if they cause trouble; keep `published: false` behaviour (three posts use it; they must not be built).
- Copy `images/` and the four linked `assets/` files (section 3) so existing URLs keep working.

### 8.3 Things that must survive

- `CNAME` (`benninger.ca`), `keybase.txt`, `favicon.ico`, `robots.txt`, `LICENSE`.
- Feeds at both `/feed.xml` and `/atom.xml` (Atom, full or summary content is builder's call; same entries as today).
- `/sitemap.xml`.
- `llms.txt` and `llms-full.txt`, generated at build time from the posts with the same structure as today (update the "Other" links to include Projects).
- Analytics: GoatCounter only (same endpoint, `benninger.goatcounter.com`). Remove Cloudflare Web Analytics (D12).
- Basic SEO and social tags: title, description, canonical, Open Graph image (a pixel-art social card is a nice-to-have).

### 8.4 Deployment

- New GitHub Actions workflow downloads the pinned Zola release, builds the site, and deploys with the official Pages actions (`actions/upload-pages-artifact`, `actions/deploy-pages`).
- Cutover requires switching the repo's Pages source from "legacy branch build" to "GitHub Actions". This is a repo-settings change and the moment the live site changes; Chris does it, or the builder does it only with his explicit go-ahead.
- All work happens on a branch. The live site stays on the current Jekyll build until cutover. Build and preview locally first.
- After cutover, remove the Jekyll files (`_config.yml`, `Gemfile*`, `_layouts/`, `_includes/`, `.bundle`, `vendor/`, `.jekyll-cache`, `_site`) and the dead theme leftovers listed in section 3, keeping the four linked `assets/` files.
- Add `.superpowers/` to `.gitignore`.

### 8.5 Quality bar

- Lighthouse (or equivalent) performance and accessibility both 95+ on Home, Projects and a long post.
- Text contrast meets WCAG AA against `bg` and `panel`. Check green-on-dark links and muted text in particular.
- Visible keyboard focus styles (an LED-style outline fits the theme).
- Responsive down to 360px wide; project cards stack on mobile.
- No client JavaScript required to read any page. Small optional JS (for example the breathing LED, if not pure CSS) is fine.

## 9. Decisions

All made or approved by Chris.

- D1. Dark, techie look with LED-style glow; blocky feel, monospace, pixel art, dark colours.
- D2. Original design; nothing copied from karamian.am, including its colours.
- D3. Home-lab rack direction with the Graphite + phosphor green palette (4.2).
- D4. Mood: home lab, workshop and hacking.
- D5. The site will host his CV, but as follow-up work after this redesign (section 7).
- D6. Drop Disqus comments for now. Reversible: Disqus or a lighter option (for example giscus) can be added later.
- D7. Zola, with a custom theme (8.1).
- D8. Status LED meanings (4.5).
- D9. Nav: Home, Projects, Posts; About kept as a page; CV slot reserved for the follow-up.
- D10. Projects page starts with davlog, Fussel and ticktick-to-todoist-migrator.
- D11. Hero art details (4.6); a warm lamp tint is allowed inside artwork only.
- D12. GoatCounter only, for privacy; drop Cloudflare Web Analytics.
- D13. The builder makes the pixel art to start. The hero is a workbench with a lamp and a disassembled server.

## 10. Open questions for Chris

None blocking this phase. The CV questions move to the follow-up (section 7).

## 11. Left to the builder

- Exact component structure, CSS organization, spacing scale, font sizes.
- Syntax-highlighting theme within the palette.
- How `.html` posts are carried over, as long as they render well and keep their URLs.
- Exact glow and shadow values, as long as they follow 4.3 and 4.4.
- Placeholder sprite designs.
- Feed content (full text or summary).
