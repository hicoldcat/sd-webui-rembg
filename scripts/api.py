
import base64
from io import BytesIO
from typing import Any, Optional

import gradio as gr
import rembg
from fastapi import Body, FastAPI
from fastapi.exceptions import HTTPException
from PIL import Image
from pydantic import BaseModel


def rembg_api(_: gr.Blocks, app: FastAPI):
    class MaskRequest(BaseModel):
        image: str = None
        model: str = None
        return_mask: bool = False
        alpha_matting: bool = False
        alpha_matting_foreground_threshold: int = 240
        alpha_matting_background_threshold: int = 10
        alpha_matting_erode_size: int = 10

    def decode_base64_to_image(encoding):
        if encoding.startswith("data:image/"):
            encoding = encoding.split(";")[1].split(",")[1]
        try:
            image = Image.open(BytesIO(base64.b64decode(encoding)))
            return image
        except Exception as err:
            raise HTTPException(
                status_code=500, detail="Invalid encoded image")

    def pil_image_to_base64(img: Image.Image) -> str:
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return img_base64

    @app.post("/rmbg-webui/image-mask")
    async def image_mask(payload: MaskRequest = Body(...)) -> Any:
        if payload.model == None:
            return

        if payload.image == None:
            return

        input_img = decode_base64_to_image(payload.image)

        mask = rembg.remove(
            input_img,
            only_mask=payload.return_mask,
            session=rembg.new_session(payload.model),
            alpha_matting=payload.alpha_matting,
            alpha_matting_foreground_threshold=payload.alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=payload.alpha_matting_background_threshold,
            alpha_matting_erode_size=payload.alpha_matting_erode_size,
        )

        response = {"image": pil_image_to_base64(mask)}

        return response


try:
    import modules.script_callbacks as script_callbacks
    script_callbacks.on_app_started(rembg_api)
except:
    print("Remove BG API failed to initialize")
