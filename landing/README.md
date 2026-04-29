# Landing Page Framework

This is a dummy framework for the MarketBrief landing page. All content is placeholder text marked with `[brackets]`.

## Structure

### Sections:
1. **Hero** - Main headline, CTA, stats
2. **Problem** - Pain points (4 cards)
3. **Solution** - How we solve it
4. **How It Works** - Process diagram (Mermaid.js) + 3 steps
5. **Features** - 6 feature cards
6. **Benefits** - 4 benefit cards
7. **Users** - 4 user types
8. **Proof** - Stats/metrics
9. **FAQ** - 6 questions
10. **Final CTA** - Strong call-to-action
11. **Footer** - Links, legal, disclaimer

## Files

- `index.html` - Main structure with placeholders
- `styles.css` - Complete styling (dark theme)
- `script.js` - Smooth scroll, animations, interactions

## Features

✅ Responsive design
✅ Dark theme (matches main app)
✅ Mermaid.js diagram support
✅ Smooth scrolling
✅ Fade-in animations
✅ Connected to main app (`../frontend/index.html`)

## How to Use

1. **Fill in content** - Replace all `[placeholder text]` with actual content
2. **Add images** - Replace `.placeholder-image` divs with real screenshots
3. **Customize colors** - Edit CSS variables in `styles.css`
4. **Test** - Open `index.html` in browser

## Navigation

- **Landing → App**: Click "Launch App" or "Try Live Demo"
- **App → Landing**: Click "Home" button in header

## Mermaid Diagram

The "How It Works" section uses Mermaid.js to render a process flow diagram. Edit the diagram in `index.html`:

```html
<div class="mermaid">
  flowchart LR
    A[Step 1] --> B[Step 2]
    B --> C[Step 3]
</div>
```

## Customization

### Colors (in `styles.css`):
```css
--primary: #3b82f6;
--secondary: #8b5cf6;
--dark: #0f172a;
```

### Content Sections:
All sections are clearly marked with comments in `index.html`. Search for `[` to find all placeholders.

## Preview

Open `landing/index.html` in your browser to see the framework.

---

**Status**: Framework ready, content needed
**Next**: Fill in all `[placeholder]` text with actual content
