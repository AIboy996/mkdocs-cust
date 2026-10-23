# mkdocs-cust

Customise the building process for my Homepage:

```yaml
plugins:
  - mkdocs-cust:
      external_link_target_blank: true
      convert_ipynb: true
      webp_redirect: true
```

- `external_link_target_blank`
  - Add `target="_blank"` attribute for external link.
- `convert_ipynb`
  - Include `.ipynb` files and convert to html.
- `webp_redirect`
  - Redirect all `*.png` link to `*.png.webp`.
- AI co-authorship is detected from the latest Git commit for each page. A
  recognized `Co-authored-by` trailer adds small, uniformly colored text after
  the page's first H1 title, right-aligned. The tool name uses a script-style
  font and reveals from left to right once. Click it to open a browser alert with
  the commit co-author's name and email. Recognized names include Claude,
  Claude Code, Codex, Copilot, Gemini, Cursor, ChatGPT, and Devin. Pages
  without a matching trailer are unchanged.
