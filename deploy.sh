#!/bin/bash
# Deploy to Cloudflare Pages
python3 scripts/build_portfolio.py || exit 1
echo "Deploying to Cloudflare Pages..."
npx wrangler pages deploy . --project-name=itogeo
echo "Done! Check https://itogeospatial.com"
