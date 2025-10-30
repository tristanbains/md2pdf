# Development Patterns

Common workflows and debugging strategies for MD2PDF development.

## Adding a New Styleable Element

When adding support for styling a new HTML element:

1. Add field to `pdf_generator.py:get_default_config()` custom_classes dict (single source of truth)
2. Add `{element}_classes: str = Form("")` to `main.py:update_config()` parameters
3. Add field to `main.py:update_config()` custom_classes dict assembly
4. Add input field to `templates/index.html` with `id="{element}_classes"`
5. Add `"{element}_classes"` to `index.html:fieldNames` array
6. Add element handling to `pdf_generator.py:apply_custom_classes()`

**Example**: Adding support for `<strong>` elements:

```python
# 1. pdf_generator.py:get_default_config()
'custom_classes': {
    # ... existing elements
    'strong': ''
}

# 2. main.py:update_config() parameters
strong_classes: str = Form("")

# 3. main.py:update_config() custom_classes assembly
'custom_classes': {
    # ... existing elements
    'strong': strong_classes
}

# 6. pdf_generator.py:apply_custom_classes()
for strong in soup.find_all('strong'):
    if self.config['custom_classes'].get('strong'):
        strong['class'] = self.config['custom_classes']['strong'].split()
```

```html
<!-- 4. templates/index.html -->
<div class="form-control">
    <label class="label">
        <span class="label-text">Strong (Bold) Classes</span>
    </label>
    <input type="text"
           id="strong_classes"
           name="strong_classes"
           value="{{ config.custom_classes.strong }}"
           class="input input-bordered" />
</div>
```

```javascript
// 5. templates/index.html:fieldNames array
const fieldNames = [
    'h1_classes', 'h2_classes', /* ... */,
    'strong_classes'  // Add here
];
```

## Debugging Temp Config Issues

When "Generate Without Saving" isn't applying settings correctly:

1. Check `temp_uploads/{uuid}.tempconfig` contains expected JSON
2. Verify `prose_color` field is present in tempconfig
3. Check browser DevTools Network tab for FormData contents
4. Add debug prints in `main.py:191-226` to trace config loading:
   ```python
   print(f"DEBUG: Looking for tempconfig at {tempconfig_path}")
   print(f"DEBUG: Tempconfig exists: {os.path.exists(tempconfig_path)}")
   print(f"DEBUG: Loaded config: {pdf_gen.config}")
   ```
5. Inspect rendered `<article>` tag in browser to verify classes applied

## Testing Prose Colors

Prose colors have SUBTLE differences between grayscale variants (slate/zinc/stone). For obvious testing:

- Use `prose-invert` for dramatic contrast (inverts all colors)
- Ensure ALL custom_classes are empty (no `text-*`, `bg-*`, `border-*` color utilities)
- Compare headings and links side-by-side
- Use browser DevTools to verify correct classes in `<article>` tag

**Quick test workflow**:
1. Set Prose Color to "slate"
2. Clear all Element Styling fields
3. Generate preview
4. Check heading colors (should be darker gray)
5. Switch to "zinc" → verify slightly warmer gray
6. Switch to "stone" → verify brownish tint

## Testing CodeHilite Themes

When adding or debugging syntax highlighting themes:

1. Check theme is in available list: Run `python -c "from pygments.styles import get_all_styles; print(list(get_all_styles()))"`
2. Verify theme dropdown is dynamically generated (not hardcoded)
3. Test theme preview gallery: `/theme-preview` should show ALL themes
4. Click theme card → verify postMessage updates main page dropdown
5. Check Pygments theme names use hyphens (e.g., `github-dark`), not underscores

## Debugging Background Process Memory

If Claude Code token usage is high:

1. Check for stale background shells: Look for `Background Bash XXXXX` warnings
2. Kill completed processes: Use `KillShell` tool or restart session
3. Commit pending git changes to eliminate diff overhead
4. Clear temp_uploads directory if cluttered

## Cross-Platform Considerations

When testing on non-macOS platforms:

- Config path defaults to `~/Library/Application Support/md2pdf/` on all platforms
  - **macOS**: Works as-is
  - **Linux**: Should use `~/.config/md2pdf/` (requires code change)
  - **Windows**: Should use `%APPDATA%\md2pdf\` (requires code change)
- Build process (`make build`) only works on macOS (py2app limitation)
- All core functionality (FastAPI, markdown processing, browser PDF) is platform-agnostic
