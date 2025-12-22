import base64
import io
from contextlib import asynccontextmanager
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException
from PIL import Image
from pydantic import BaseModel, Field
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

from chandra.model.hf import generate_hf
from chandra.model.schema import BatchInputItem
from chandra.output import parse_markdown


class PromptType(str, Enum):
    ocr_layout = "ocr_layout"
    ocr = "ocr"


class OCRRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image")
    prompt_type: PromptType = Field(default=PromptType.ocr_layout, description="Prompt type")
    custom_prompt: Optional[str] = Field(default=None, description="Custom prompt (overrides prompt_type)")


class OCRResponse(BaseModel):
    raw: str = Field(..., description="Raw model output")
    markdown: str = Field(..., description="Parsed markdown")
    token_count: int = Field(..., description="Number of tokens generated")
    error: bool = Field(default=False, description="Whether an error occurred")


model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    print("Loading model...")
    model = Qwen3VLForConditionalGeneration.from_pretrained("datalab-to/chandra").cuda()
    model.processor = AutoProcessor.from_pretrained("datalab-to/chandra")
    print("Model loaded!")
    yield
    del model


app = FastAPI(
    title="OCR Tool API",
    description="OCR API for AI Agents using Chandra model",
    version="1.0.0",
    lifespan=lifespan,
)


def decode_base64_image(image_base64: str) -> Image.Image:
    try:
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        return image
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")


@app.post("/ocr", response_model=OCRResponse)
async def ocr(request: OCRRequest):
    """Perform OCR on an image and return structured output."""
    image = decode_base64_image(request.image_base64)

    batch = [
        BatchInputItem(
            image=image,
            prompt=request.custom_prompt,
            prompt_type=request.prompt_type.value if not request.custom_prompt else None,
        )
    ]

    result = generate_hf(batch, model)[0]
    markdown = parse_markdown(result.raw)

    return OCRResponse(
        raw=result.raw,
        markdown=markdown,
        token_count=result.token_count,
        error=result.error,
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "model_loaded": model is not None}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
