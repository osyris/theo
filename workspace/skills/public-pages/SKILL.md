---
name: public_pages
description: Create publicly accessible web pages, landing pages, dashboards, forms, and widgets
metadata: {"openclaw": {"always": true}}
---

# Public Pages

You can create publicly accessible web content that users can view without authentication.

## How it works

1. Create HTML, CSS, and JavaScript files in `/data/workspace/pages/`
2. Content becomes instantly accessible at `https://{domain}/pages/`
3. No authentication required - anyone with the URL can view

## Directory structure

```
/data/workspace/pages/
├── index.html          → /pages/
├── about.html          → /pages/about.html
├── contact/
│   └── index.html      → /pages/contact/
├── css/
│   └── styles.css      → /pages/css/styles.css
└── js/
    └── app.js          → /pages/js/app.js
```

## When to use this skill

Use this when users ask you to:
- Create a landing page
- Build a portfolio or showcase
- Generate a lead capture or contact form
- Create a dashboard or data visualization
- Build any publicly shareable web content
- Make a widget or embeddable component

## Guidelines

1. **Create the pages directory first** if it doesn't exist:
   ```bash
   mkdir -p /data/workspace/pages
   ```

2. **Use relative paths** for CSS/JS assets within pages

3. **Single-file approach** is often best - inline CSS and JS in HTML for simple pages

4. **For complex pages**, organize assets in subdirectories:
   - `/data/workspace/pages/project-name/index.html`
   - `/data/workspace/pages/project-name/styles.css`
   - `/data/workspace/pages/project-name/script.js`

5. **Supported file types**: HTML, CSS, JS, JSON, images (PNG, JPG, GIF, SVG, WebP, ICO), fonts (WOFF, WOFF2, TTF), video (MP4, WebM)

## Example

To create a simple landing page:

```bash
cat > /data/workspace/pages/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }
    </style>
</head>
<body>
    <h1>Welcome to My Page</h1>
    <p>This content is publicly accessible.</p>
</body>
</html>
EOF
```

The page is immediately available at `/pages/` or `/pages/index.html`.
