import os
import io
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

# This function assumes that an environment variable 'STABILITY_KEY' has already been set.
def stability_setup():
    os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

    stability_api = client.StabilityInference(
        key=os.environ['STABILITY_KEY'],
        verbose=True,
        engine="stable-diffusion-xl-beta-v2-2-2",
    )
    return stability_api


def generate_image(api, img_prompt, dims: tuple):    
    answers = api.generate(
        prompt=img_prompt,
        cfg_scale=8.0,
        width=dims[0], # Generation width, defaults to 256 if not included.
        height=dims[1], # Generation height, defaults to 256 if not included.
    )

    # Set up our warning to print to the console if the adult content classifier is tripped.
    # If adult content classifier is not tripped, save generated images.
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                
                return img
                