#!/usr/bin/env bash
# Deploy the Expo web export to Vercel (project "dist", prod domain
# dist-nine-kappa-20.vercel.app).
#
# Why this script exists: `expo export` WIPES dist/ — including dist/vercel.json
# (cleanUrls config the static routes depend on) and dist/.vercel (the project
# link). Deploying a bare export silently breaks /privacy, /terms, etc.
set -euo pipefail
cd "$(dirname "$0")/.."   # mobile/

BACKUP=".vercel-backup"
mkdir -p "$BACKUP"
[ -f dist/vercel.json ] && cp dist/vercel.json "$BACKUP/vercel.json"
if [ -d dist/.vercel ]; then rm -rf "$BACKUP/.vercel"; cp -R dist/.vercel "$BACKUP/.vercel"; fi

npx expo export --platform web

if [ -f "$BACKUP/vercel.json" ]; then
  cp "$BACKUP/vercel.json" dist/vercel.json
else
  printf '{\n  "cleanUrls": true,\n  "trailingSlash": false\n}\n' > dist/vercel.json
fi
if [ -d "$BACKUP/.vercel" ]; then
  cp -R "$BACKUP/.vercel" dist/.vercel
fi

npx vercel deploy dist --prod --yes
