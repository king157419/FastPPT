# Glossary

- `TeachingSpec`: normalized teaching intent object compiled from raw chat or form input.
- `preflight`: required fields that must be provided before generation, currently teaching goal, audience, and difficulty focus.
- `slides_json`: intermediate courseware JSON used for preview, revise, and export.
- `blocks[]`: normalized page content blocks attached to a page for more structured rendering and export.
- `Mode A`: teacher-led execution or update flow with stronger structure preservation.
- `Mode B`: co-creation flow with guided clarification and option-based collaboration.
- `Mode C`: full-auto generation path, useful but not the main quality bar.
- `evidence`: source snippets or metadata attached to generated content for traceability.
- `plain chat path`: contest-safe chat runtime that avoids agent and Redis dependencies.
- `revise loop`: editing path that updates existing `slides_json` rather than generating from scratch.

