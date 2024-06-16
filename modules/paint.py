import os

from PIL.Image import Image
from dotenv import load_dotenv
from horde_sdk.ai_horde_api import KNOWN_SAMPLERS
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateAsyncRequest,
    ImageGenerationInputPayload,
)

load_dotenv()

API_KEY = os.getenv("HORDE_API_KEY")


def paint(prompt: str) -> Image:
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
            prompt=prompt,
            models=["AlbedoBase XL (SDXL)"],
        ),
    )

    if len(status_response.generations) == 0:
        raise Exception("No generations found")

    image = simple_client.download_image_from_generation(status_response.generations[0])
    image.save("image.webp")

    return image
