#!/bin/bash
# Deploy to Cloudflare Pages
echo "Deploying to Cloudflare Pages..."
npx wrangler pages deploy . --project-name=itogeo
echo "Done! Check https://itogeospatial.com"
