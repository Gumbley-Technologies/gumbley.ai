# Gumbley AI — the rebrand, and how to keep it through upstream updates

This repository is a fork of [Open WebUI](https://github.com/open-webui/open-webui)
serving **gumbley.ai**. The product is Open WebUI; the skin, the name and the
sign-in are Gumbley's. This file is the contract for that skin: what it is,
where it lives, and what to run after every upstream update.

The design it targets is `design/Gumbley AI.dc.html` — open it in a browser.
It is a reference, not code to copy; the handoff's own instruction is *"Adapt
as needed — Open WebUI's DOM stays; restyle it to match the prototype's palette
and typography."* That is the scope: **palette, typography, artwork, name and
sign-in.** Message bubbles, menus and layout stay Open WebUI's.

---

## The one thing to know

**Almost nothing about this rebrand is a source edit.** It is a directory of
files (`branding/`) that overlays a directory upstream already ships, plus one
environment variable and one three-line patch. That is deliberate: the smaller
the diff against upstream, the less there is to break when upstream moves.

| What | Where | Survives an upstream change? |
|---|---|---|
| Palette, typography, chrome, sign-in | `branding/css/*.css` → `custom.css` | Yes — `custom.css` is upstream's own extension point and ships empty |
| Logos, favicons, splash, fonts | `branding/static/` | Yes — our filenames overlay theirs; theirs stay |
| Pre-hydration title, theme colour | `branding/static/loader.js` | Yes — `loader.js` is also upstream's, also ships empty |
| The installed-app identity (PWA) | `branding/static/manifest.json` + `EXTERNAL_PWA_MANIFEST_URL` | Yes — that variable is upstream's own hook |
| The product name everywhere in the UI | `WEBUI_NAME` env var | Yes — no code involved |
| Dropping the `" (Open WebUI)"` suffix | `backend/open_webui/env.py` | **Anchored patch.** Fails loudly if upstream moves it |
| `APP_NAME`, `<title>` | `src/lib/constants.ts`, `src/app.html` | **Anchored patches.** Only affect builds from this tree |

### Why the CSS can do so much

Open WebUI is Tailwind v4, and Tailwind v4 emits its colour scale as real CSS
custom properties inside `@layer theme`. Two consequences:

* Redefining `--color-gray-50 … --color-gray-950` re-tints **every**
  `bg-gray-900`, `dark:text-gray-400`, `border-gray-200` in the app at once.
  No component selectors, so no component refactor can break it.
* `custom.css` is loaded in `<head>` **before** SvelteKit injects the app
  stylesheet — which does not matter, because unlayered declarations beat
  layered ones regardless of source order.

`src/tailwind.css` also sets `font-family: var(--app-font-family, …)` on `html`,
so a single line re-fonts the whole UI.

---

## The PWA

gumbley.ai installs as its own app — its own icon, its own window, its own
entry in the launcher and task switcher. That is a manifest, and it is the same
shape as everything else here: a file in the overlay plus one environment
variable, no source edit.

`backend/open_webui/main.py` serves `/manifest.json` itself, generating a stock
one from `WEBUI_NAME` unless **`EXTERNAL_PWA_MANIFEST_URL`** is set — in which
case it fetches that URL and returns its JSON verbatim. That variable is set on
the container (see the infra repo's `infra/gumbley-ai/docker-compose.yml`) and
points back at this overlay:

```
EXTERNAL_PWA_MANIFEST_URL: http://127.0.0.1:8080/static/manifest.json
```

Three things about that line are load-bearing:

* **It is a loopback URL, not `https://gumbley.ai/…`.** The fetch happens
  inside the container. Going out to the public name would put DNS, TLS, the
  nginx rate limiter and the hairpin route between the app and its own manifest,
  and `main.py` calls `raise_for_status()` — any of them failing turns
  `/manifest.json` into a 500 and the app stops being installable. On loopback
  the only way it fails is the app being down, in which case nothing is being
  served anyway.
* **The file must be `.json`, not `.webmanifest`.** That fetch ends in aiohttp's
  `r.json()`, which enforces `application/json` and raises `ContentTypeError` on
  anything else. `StaticFiles` serves `.webmanifest` as
  `application/manifest+json` — correct per spec, and fatal here. (The browser
  never sees this filename: it fetches `/manifest.json`, which is the route.)
* **`/static/` is unauthenticated**, which it has to be — the browser fetches
  the manifest and its icons before anyone signs in.

### The icons

Three, and the third is the one people get wrong:

| Icon | Purpose | Must it be opaque? |
|---|---|---|
| `web-app-manifest-192x192.png`, `-512x512.png` | `any` | No — transparent, the surface composites it |
| `web-app-manifest-maskable-512x512.png` | `maskable` | **Yes**, to the edges |
| `apple-touch-icon.png` (`<link>` in `app.html`, not the manifest) | iOS home screen | **Yes** — iOS composites transparency onto **black** |

A `maskable` icon is cropped by the launcher to whatever shape it likes, so the
art has to survive a circle of 80% diameter. The lock-up is full-bleed, so
`build-assets.sh` scales it to 78% and centres it on the light brand canvas.
The favicon generator's old `site.webmanifest` — now deleted — declared the
**un-padded** lock-up as `maskable`, which slices the wordmark off on every
Android launcher. Both opaque icons sit on `#f4f9fd` rather than the brand
navy: the shield's own interior is navy, so on navy it loses its outline.

### What it does not do

There is **no service worker**, so there is no offline mode and no automatic
install banner — Chrome's prompt heuristic still wants a fetch handler.
Installing from the browser menu works: Chrome dropped the service-worker
requirement for that in 108 (mobile) / 112 (desktop). This is not an oversight
to fix later — Open WebUI ships no service worker and `src/routes/+layout.svelte`
actively *unregisters* any it finds, as its mechanism for forcing a clean reload
after a frontend update. Adding one would fight that.

One thing to watch on first install: sign-in leaves the scope (`/`) for
`sso.gumbleytechnologies.com` and comes back. Chrome handles an out-of-scope
navigation in an in-app tab and returns to the app window once the redirect
lands back on `gumbley.ai` — the normal OAuth-in-a-PWA path — but it has not
been exercised from an actually-installed window yet. Try it at first install.

---

## After an upstream update

There are two update paths and they are independent.

### 1. Bumping the deployed image (the common one)

The deployed image is **the official Open WebUI release plus `branding/`** —
see `deploy/Dockerfile`. It is not built from this tree.

> **Where the compose project lives.** This repo is a *public* fork (GitHub
> will not let a public fork be made private), so the compose file — which
> names the Keycloak issuer, the realm, the role claim and the state path —
> is kept in the private infrastructure repo, alongside the nginx vhost and
> the rest of the estate. This repo carries the rebrand and the Dockerfile;
> that one carries the runbook. Nothing here needs a secret.

Upgrading is: bump `OPEN_WEBUI_VERSION`, rebuild, **verify**, restart.

```bash
scripts/branding/verify-image.sh gumbley-ai:0.11.4   # <-- do not skip this
```

`verify-image.sh` greps the **built image** for every id and custom property
the CSS depends on. That check matters more than it looks: if upstream renames
`#auth-login-card`, the sign-in rules simply stop matching. Nothing errors,
nothing breaks — the page just quietly reverts to stock Open WebUI, which is
exactly the sort of regression a health check never catches.

The `env.py` patch is applied during the image build and **fails the build** if
its anchor has moved, so a bad bump cannot ship silently.

### 2. Merging upstream into this fork

```bash
git remote add upstream https://github.com/open-webui/open-webui.git   # once
git fetch upstream
git merge upstream/main
scripts/branding/apply.sh                 # re-applies + re-checks every anchor
```

`apply.sh` regenerates `custom.css`, re-copies the overlay into `static/static/`,
re-applies the three name patches, and asserts that the CSS anchors still exist.
`--check` does all of it read-only, which is the form to put in CI.

> This clone is **shallow** (`git clone --depth`). `git fetch --unshallow` first,
> or the merge will not find a common ancestor.

### The two trees may sit on different versions

They currently do: this tree is upstream `0.11.2`, the deployed image is
`0.11.3`. That is fine and expected — the deployment is an overlay, not a build
of this tree — and it is why `verify-image.sh` checks the image rather than the
source. Close the gap with path 2 whenever convenient.

---

## Files

```
branding/
  css/00-fonts.css      self-hosted Outfit + Nunito Sans @font-face rules
  css/10-palette.css    the grey ramp, the blue ramp, the accent, the UI font
  css/20-chrome.css     send button, links, scrollbars, splash, selection
  css/30-auth.css       the sign-in gate
  static/               everything that overlays the app's /static route,
                        INCLUDING the generated custom.css and the fonts
  static/manifest.json  the PWA manifest, hand-written — this is the installed
                        app's identity. EXTERNAL_PWA_MANIFEST_URL points at it
scripts/branding/
  apply.sh              apply/verify the brand on this working tree
  patch-source.py       the three anchored name patches
  build-assets.sh       regenerate branding/static/*.png|ico|svg from design/assets/
  verify-image.sh       verify a BUILT image is branded
deploy/
  Dockerfile            official release + branding/  (a ~1 second build)
```

The compose project, its `.env.example` and the deployment runbook are in the
private infrastructure repo — see the note under "Bumping the deployed image".

`branding/static/custom.css` is **generated** — edit `branding/css/*.css` and
run `scripts/branding/apply.sh`.

`static/static/` holds a **copy** of that overlay, committed on purpose. The
deployed image does not read it (`deploy/Dockerfile` copies `branding/static/`
straight onto the release), but a build from this tree does — and so does
`npm run dev`. Without the copy, a from-source run would load a `custom.css`
whose `@font-face` and logo URLs point at files that are not there. The extra
~370 KB in git buys a fork you can check out and run.

---

## Licence

Open WebUI's licence (clause 4) prohibits altering or replacing Open WebUI
branding **except** — clause 4(i) — for deployments where the number of end
users does not exceed **fifty (50) in any rolling thirty (30) day period**.
That allowance is what this rebrand stands on.

**What that obliges:**

* **Stay under fifty users.** Check the count in the admin panel (Admin Panel →
  Users). Past fifty, either obtain an enterprise licence or revert the
  branding — reverting is `git revert` on the branding commit plus dropping
  `WEBUI_NAME`, because everything is additive.
* **Leave the licence intact.** `LICENSE`, `LICENSE_HISTORY`, `LICENSE_NOTICE`,
  `CONTRIBUTOR_LICENSE_AGREEMENT`, every in-source licence header and every
  `BRANDING.md` / `README.md` upstream ships under `static/` are untouched, and
  must stay that way. Nothing in `scripts/branding/` removes one.

---

## Deliberate deviations

**From the design reference**

* **The light-mode canvas is `#ffffff`, not `#f4f9fd`.** Open WebUI paints the
  canvas with `bg-white` and the composer with `bg-white` too. Retinting
  `--color-white` would flatten the composer against the canvas and tint every
  `text-white`, so the canvas keeps pure white and the sidebar takes the
  design's `#eaf2f8`. The layering the design is after is preserved; the exact
  value is off by about 2%. Dark mode — the design's default, and the one in
  the screenshot — matches exactly.
* **Message bubbles keep Open WebUI's shape.** The design's asymmetric
  `5px 16px 16px 16px` bubble would mean chasing component classes that change
  between releases, against an explicit "the DOM stays" instruction.
* **The webfonts come from the marketing site's build, not Google's CDN.** Same
  two faces, same subsets, self-hosted, so `font-src 'self'` holds on the
  gumbley.ai CSP.

**From the Host Architecture doc**

* **Memory limit is 1536M, not §10's 768M.** §10 assumes "OpenWebUI stays small
  with inference off-box", which is true of chat and false of this container:
  RAG's embedding model runs locally and `main.py` loads it during startup
  whether or not anyone uploads a document. Measured here it reaches ~990 MiB
  RSS during that load. At 768M the kernel OOM-kills it mid-load and
  `unless-stopped` restarts it forever — a boot loop, not a tight fit.
* **The image floor is 0.11.3.** Upstream `0.11.2` cannot start against an
  empty database at all: `config.py` runs alembic partway through its own module
  body, the migration imports `config` back, and the resulting circular import
  aborts every migration — after which the app dies on `no such table: config`.
  Reproduced on the stock upstream image with no Gumbley layer present.

---

## Not done yet

**There is no model provider configured.** `ENABLE_OLLAMA_API=false` (there is
no Ollama on this host) and no OpenAI-compatible connection is set, so the chat
has nothing to answer with. Sign-in, the brand, the admin panel and the whole
UI work; sending a message will not. Add a connection in Admin Panel →
Settings → Connections, or set `OPENAI_API_BASE_URL` / `OPENAI_API_KEY` on the
container.

The design's model menu — Gumbley Core / Reason / Local — is naming for those
connections once they exist, not something the rebrand creates.
