#!/usr/bin/env bash
# Regenerate branding/static/*.png|ico|svg from the design assets in design/assets/.
#
# The outputs ARE committed — deploying must not need ImageMagick. Run this only
# when a design asset changes, then commit what it produces.
#
# Requires: ImageMagick 7 (`magick`).
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
src="$here/design/assets"
out="$here/branding/static"

command -v magick >/dev/null || { echo "magick (ImageMagick 7) not found" >&2; exit 1; }
mkdir -p "$out"

# The brand art is a densely shaded illustration, so truecolour PNG lands at
# ~550 KB for the sign-in hero alone — on the critical path of a page that has
# not authenticated anyone yet. Quantising to 255 colours (one slot reserved
# for transparency) is a 4-5x cut with no visible loss on flat-shaded artwork.
# `-strip` drops the colour profile and EXIF the design tool left behind.
opt=(-strip -colors 255 -define png:compression-level=9)

# Which source art goes where. The design reference itself
# (design/Gumbley AI.dc.html) points the browser tab at favicon.png — the flat
# "G" shield — and keeps the full mascot lock-up for places with room for it.
# Anything under ~96px gets the shield; anything above gets the lock-up.
shield="$src/favicon.png"          #  64x64  flat G shield
icon192="$src/gumbleyai-icon-192.png"
icon512="$src/gumbleyai-icon-512.png"
logo="$src/gumbleyai-logo.png"     # 1536x1024 mascot + wordmark, transparent

echo "→ browser tab (the shield)"
cp "$shield" "$out/favicon.png"
# 64 → 96 is a mild upscale; the mark is flat colour so it survives it.
magick "$shield" -filter Lanczos -resize 96x96 "$out/favicon-96x96.png"
magick "$shield" -define icon:auto-resize=48,32,16 "$out/favicon.ico"

# An SVG favicon is preferred by browsers over every PNG hint in <head>, so it
# has to exist and has to be ours — otherwise the tab keeps Open WebUI's mark
# no matter how many PNGs we replace. There is no vector master, so this wraps
# the raster at 2x in a viewBox that scales cleanly.
python3 - "$shield" "$out/favicon.svg" <<'PY'
import base64, sys
raw = base64.b64encode(open(sys.argv[1], 'rb').read()).decode()
open(sys.argv[2], 'w').write(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<image href="data:image/png;base64,%s" width="64" height="64"/>'
    '</svg>\n' % raw
)
PY

echo "→ app icons (the lock-up)"
magick "$icon512" -resize 180x180 "${opt[@]}" "$out/apple-touch-icon.png"
# main.py's generated /manifest.json declares /static/logo.png as 500x500.
magick "$icon512" -resize 500x500 "${opt[@]}" "$out/logo.png"
magick "$icon192" "${opt[@]}" "$out/web-app-manifest-192x192.png"
magick "$icon512" "${opt[@]}" "$out/web-app-manifest-512x512.png"

echo "→ splash + sign-in art"
# app.html preloads splash-dark.png on dark, splash.png on light, and sizes it
# by height. Both themes get the same transparent lock-up.
magick "$logo" -resize 600x400 "${opt[@]}" "$out/splash.png"
cp "$out/splash.png" "$out/splash-dark.png"
# Sign-in hero: the design draws it at min(500px, 88vw), so 2x is 1000 wide.
magick "$logo" -resize 1000x667 "${opt[@]}" "$out/gumbleyai-logo.png"

echo "→ 'brought to you by' wordmark"
# Sourced from the marketing site's public assets — the same file gumbleytechnologies.com serves.
magick "$src/gumbley-wordmark.png" -resize 330x "${opt[@]}" "$out/gumbley-wordmark.png"

echo
magick identify -format '%f  %wx%h  %b\n' "$out"/*.png "$out"/*.ico
