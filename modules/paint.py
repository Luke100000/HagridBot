import requests
from pipeline.cloud.pipelines import run_pipeline


def paint(topic):
    output = run_pipeline(
        "paulh/open-journey-xl:latest",
        topic,
        dict(
            guidance_scale=7.5,
            height=1024,
            negative_prompt="worst quality, normal quality, low quality, low res, blurry, text, watermark, logo, banner, extra digits, cropped, jpeg artifacts, signature, username, error, sketch ,duplicate, ugly, monochrome, horror, geometry, mutation, disgusting",
            num_images_per_prompt=1,
            num_inference_steps=30,
            width=1024,
        )
    )

    url = output.result.outputs[0].value[0]["file"]["url"]
    img_data = requests.get(url).content
    with open('image.jpg', 'wb') as handler:
        handler.write(img_data)