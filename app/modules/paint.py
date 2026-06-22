from pathlib import Path

import replicate

from app.config import get_data_path

MODEL = "black-forest-labs/flux-2-klein-9b"


def paint(prompt: str) -> Path:
    output = replicate.run(
        MODEL,
        input={
            "prompt": prompt,
            "aspect_ratio": "1:1",
            "output_format": "webp",
            "output_quality": 90,
            "go_fast": True,
        },
    )

    path = get_data_path("image.webp")
    image = next(iter(output))
    with open(path, "wb") as f:
        f.write(image.read())

    return path
