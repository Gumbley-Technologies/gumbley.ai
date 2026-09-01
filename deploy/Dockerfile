# syntax=docker/dockerfile:1
#
# Gumbley AI — the deployed image.
#
# This is a THIN LAYER over the official Open WebUI release, not a build of
# this fork. Two lines of substance: overlay the brand assets, drop the name
# suffix. It exists in this shape because of how the rebrand is structured —
# see BRANDING.md — and it buys two things:
#
#   * Upgrading is `OPEN_WEBUI_VERSION=x.y.z docker compose build` and a
#     restart. Seconds, not the twenty-plus minutes a full frontend + torch
#     build takes, and no chance of the build drifting from upstream's.
#   * The branding is provably additive. Everything Gumbley about the running
#     container is in the two RUN/COPY lines below; nothing else is touched.
#
# The fork's own sources carry the same patches (scripts/branding/apply.sh) so
# a from-source build or `npm run dev` looks identical. That path is the
# fallback, not the deployment.
#
# LICENCE: the Open WebUI licence permits replacing its branding for
# deployments under 50 end users in a rolling 30 days. That is the basis this
# image relies on. Every LICENSE file, licence header and copyright notice is
# left in place. Read BRANDING.md before scaling past that.

# 0.11.3 is the FLOOR, not just the current pick: 0.11.2 cannot start against
# an empty database at all. config.py runs alembic partway through its own
# module body, the migration imports config back, and the circular import
# aborts every migration — so the app then dies on "no such table: config".
# Reproduced on the stock upstream image before any Gumbley layer was added.
ARG OPEN_WEBUI_VERSION=0.11.3
FROM ghcr.io/open-webui/open-webui:${OPEN_WEBUI_VERSION}

# /app/build/static is the built frontend's static directory, and it is the
# SOURCE of truth at runtime: backend/open_webui/config.py empties
# /app/backend/open_webui/static on every boot and re-copies from here. Overlay
# anywhere else and the first restart quietly undoes it.
COPY branding/static/ /app/build/static/

# The one thing a file overlay cannot reach: env.py appends " (Open WebUI)" to
# any WEBUI_NAME that is not the default. The patcher is anchored on the exact
# upstream text and exits non-zero if it has moved, so an upstream bump that
# changes it fails the BUILD rather than silently shipping the wrong name.
COPY scripts/branding/patch-source.py /tmp/patch-source.py
RUN python3 /tmp/patch-source.py --root /app && rm /tmp/patch-source.py
