# 啟動 OCR Tools

cd /media/moci/NVME21/projects/ai-agent-tools/tools/ocr_tool
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8001