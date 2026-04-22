# Flow: generate-courseware

1. Upload materials and parse them into chunks plus source metadata.
2. Collect or complete `TeachingSpec`.
3. Run retrieval and optional knowledge enrichment.
4. Generate raw slide JSON.
5. Attach evidence.
6. Normalize blocks.
7. Preview.
8. Export PPTX and DOCX.

## Main entry points

- `backend/api/upload.py`
- `backend/api/chat.py`
- `backend/api/generate.py`
- `frontend/src/components/FileUpload.vue`
- `frontend/src/components/ChatPanel.vue`
- `frontend/src/components/GenerateBtn.vue`
- `frontend/src/components/PreviewPanel.vue`

