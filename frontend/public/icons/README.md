# PWA Icons

Placeholder directory. The app manifest (`/public/manifest.json`) references:

- `icon-192.png` (192x192) — home screen / launcher
- `icon-512.png` (512x512) — splash screen
- `icon-maskable-512.png` (512x512, purpose=maskable) — adaptive icons

Generate these from the DSI logo (`/public/Standard_Generate_Logo_and_DSI.svg`) using e.g.:

```bash
# Requires imagemagick or equivalent
convert -background '#000' -resize 192x192 logo.svg icon-192.png
convert -background '#000' -resize 512x512 logo.svg icon-512.png
convert -background '#000' -resize 512x512 -gravity center -extent 512x512 \
        logo.svg icon-maskable-512.png
```

Until the real assets are committed the browser will fall back to the
default favicon — installability still works, the icon just won't look
branded.
