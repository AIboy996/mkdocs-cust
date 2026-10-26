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
- AI co-authorship is determined from all Git commits for each page. Counts are
  aggregated by recognized AI tool (for example, "Claude" and "Claude Code"
  count as the same signer); the tool appearing in the most commits is shown,
  and ties go to the tool whose first co-authored commit is earliest (if both
  first appear in the same commit, the earlier trailer wins). The tool
  name appears as small, uniformly colored text after the page's first H1
  title, right-aligned. It uses a script-style font and reveals from left to
  right once. Click it to open a browser alert with the co-author's name and
  email. Recognized names include Claude, Claude Code, Codex, Copilot, Gemini,
  Cursor, ChatGPT, Devin, and DeepSeek. Pages without a matching trailer are
  unchanged.
