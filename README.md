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
