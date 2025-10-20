import os
from pathlib import Path

from dotenv import load_dotenv
from horde_sdk.ai_horde_api import KNOWN_SAMPLERS
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateAsyncRequest,
    ImageGenerationInputPayload,
)

from app.config import get_data_path

load_dotenv()

API_KEY = os.getenv("HORDE_API_KEY")


def paint(prompt: str) -> Path:
    simple_client = AIHordeAPISimpleClient()

    status_response, job_id = simple_client.image_generate_request(
        ImageGenerateAsyncRequest(
            apikey=API_KEY,
            params=ImageGenerationInputPayload(
                sampler_name=KNOWN_SAMPLERS.k_euler,
                width=1024,
                height=1024,
                steps=30,
                use_nsfw_censor=False,
                n=1,
            ),
            slow_workers=False,
            prompt=prompt,
            models=["AlbedoBase XL (SDXL)", "Juggernaut XL"],
        ),
    )

    if len(status_response.generations) == 0:
        raise Exception("No generations found")

    if status_response.generations[0].censored:
        raise Exception("Generated image was censored")

    path = get_data_path("image.webp")
    image = simple_client.download_image_from_generation(status_response.generations[0])
    image.save(path)

    return path
