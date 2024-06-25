import sys
import torch

import os
import sys
import folder_paths

comfy_path = os.path.dirname(folder_paths.__file__)

if 'ComfyUI-Unique3D' not in comfy_path:
    unique3d_path = os.path.join(comfy_path, 'custom_nodes', 'ComfyUI-Unique3D')

    sys.path.append(unique3d_path)
else:
    unique3d_path = comfy_path

from PIL import Image
import numpy as np
from rembg import remove
from ..utils import change_rgba_bg, rgba_to_rgb
from ..custom_models.utils import load_pipeline
from ...scripts.all_typing import *
from ...scripts.utils import session, simple_preprocess

training_config = f"{unique3d_path}/app/custom_models/image2mvimage.yaml"
checkpoint_path = f"{unique3d_path}/ckpt/img2mvimg/unet_state_dict.pth"
trainer, pipeline = load_pipeline(training_config, checkpoint_path)
# pipeline.enable_model_cpu_offload()

def predict(img_list: List[Image.Image], guidance_scale=2., **kwargs):
    if isinstance(img_list, Image.Image):
        img_list = [img_list]
    img_list = [rgba_to_rgb(i) if i.mode == 'RGBA' else i for i in img_list]
    ret = []
    for img in img_list:
        images = trainer.pipeline_forward(
            pipeline=pipeline,
            image=img,
            guidance_scale=guidance_scale, 
            **kwargs
        ).images
        ret.extend(images)
    return ret


def run_mvprediction(input_image: Image.Image, remove_bg=True, guidance_scale=1.5, seed=1145):
    if input_image.mode == 'RGB' or np.array(input_image)[..., -1].mean() == 255.:
        # still do remove using rembg, since simple_preprocess requires RGBA image
        print("RGB image not RGBA! still remove bg!")
        remove_bg = True

    if remove_bg:
        input_image = remove(input_image, session=session)

    # make front_pil RGBA with white bg
    input_image = change_rgba_bg(input_image, "white")
    single_image = simple_preprocess(input_image)

    generator = torch.Generator(device="cuda").manual_seed(int(seed)) if seed >= 0 else None

    rgb_pils = predict(
        single_image,
        generator=generator,
        guidance_scale=guidance_scale,
        width=256,
        height=256,
        num_inference_steps=30,
    )

    return rgb_pils, single_image
