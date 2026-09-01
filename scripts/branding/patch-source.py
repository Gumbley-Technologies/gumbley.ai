#!/usr/bin/env python3
"""Apply (or verify) the Gumbley AI name patches.

Almost the whole rebrand is data — branding/static/ overlays the built
frontend's asset directory, and WEBUI_NAME comes from the environment. Three
places cannot be reached that way, and this file is all three of them.

Every patch is ANCHORED on the exact upstream text. That is the point: after
`git merge upstream/main` this either applies cleanly, reports "already
applied", or fails naming the file whose anchor moved. It never edits
something that has silently changed shape underneath it.

  patch-source.py            apply, in place, idempotently
  patch-source.py --check    verify only; exit 1 if anything is unapplied
  patch-source.py --root DIR run against a different tree (the deploy image
                             layers this over /app, where env.py lives at
                             backend/open_webui/ but there is no src/)

Nothing here removes an Open WebUI copyright notice, licence file or licence
header — see BRANDING.md for what the licence does and does not allow.
"""

import argparse
import pathlib
import sys

BRAND = 'Gumbley AI'

PATCHES = [
    {
        'path': 'backend/open_webui/env.py',
        'why': (
            'env.py appends " (Open WebUI)" to any WEBUI_NAME that is not the '
            'default, so setting the env var alone yields "Gumbley AI (Open '
            'WebUI)". Dropping the suffix is the one change the licence '
            'actually gates — see BRANDING.md.'
        ),
        'find': (
            "WEBUI_NAME = os.getenv('WEBUI_NAME', 'Open WebUI')\n"
            "if WEBUI_NAME != 'Open WebUI':\n"
            "    WEBUI_NAME += ' (Open WebUI)'\n"
        ),
        'replace': (
            "WEBUI_NAME = os.getenv('WEBUI_NAME', 'Open WebUI')\n"
            "# GUMBLEY: upstream appends ' (Open WebUI)' here. Removed under the\n"
            "# LICENSE clause 4(i) <=50-user allowance; see BRANDING.md.\n"
        ),
    },
    {
        'path': 'src/lib/constants.ts',
        'why': (
            'APP_NAME seeds the WEBUI_NAME store before the backend config '
            'arrives (src/lib/stores/index.ts). Only visible for the moment '
            'between first paint and mount, but it is the name a from-source '
            'dev server shows.'
        ),
        'find': "export const APP_NAME = 'Open WebUI';",
        'replace': "export const APP_NAME = '%s';" % BRAND,
    },
    {
        'path': 'src/app.html',
        'why': (
            'The pre-hydration document title. branding/static/loader.js also '
            'corrects this at runtime, which is what covers the deployed image '
            '(built from upstream, not from this tree) — but a build made from '
            'this repo should not need the runtime fix.'
        ),
        'find': '<title>Open WebUI</title>',
        'replace': '<title>%s</title>' % BRAND,
    },
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='verify only, change nothing')
    ap.add_argument('--root', default=None, help='tree to patch (default: repo root)')
    args = ap.parse_args()

    root = pathlib.Path(args.root) if args.root else pathlib.Path(__file__).resolve().parents[2]

    applied, already, missing, failed = 0, 0, 0, 0

    for p in PATCHES:
        target = root / p['path']
        label = p['path']

        if not target.exists():
            # Expected when running --root against the deploy image, which has
            # the backend but no frontend sources.
            print('  ~  %-32s not present, skipped' % label)
            missing += 1
            continue

        text = target.read_text()

        if p['replace'] in text and p['find'] not in text:
            print('  =  %-32s already branded' % label)
            already += 1
            continue

        if p['find'] not in text:
            print('  !  %-32s ANCHOR NOT FOUND' % label, file=sys.stderr)
            print('     upstream changed this. Expected to find:', file=sys.stderr)
            for line in p['find'].rstrip('\n').split('\n'):
                print('       | %s' % line, file=sys.stderr)
            print('     why it is patched: %s' % p['why'], file=sys.stderr)
            failed += 1
            continue

        if args.check:
            print('  x  %-32s not branded' % label, file=sys.stderr)
            failed += 1
            continue

        target.write_text(text.replace(p['find'], p['replace']))
        print('  +  %-32s branded' % label)
        applied += 1

    print(
        '\n%s: %d applied, %d already, %d skipped, %d failed'
        % ('check' if args.check else 'patch', applied, already, missing, failed)
    )
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
