import os
import sys
import folder_paths
import torch

comfy_path = os.path.dirname(folder_paths.__file__)

unique3d_path = f'{comfy_path}/custom_nodes/ComfyUI-Unique3D'

sys.path.append(unique3d_path)

parent_dir = os.path.dirname(comfy_path)
python_embeded_path = os.path.join(parent_dir, 'python_embeded', 'Scripts')

os.environ['PATH'] = os.environ['PATH'] + ";" + python_embeded_path

from .app.all_models import model_zoo
from PIL import Image
from pytorch3d.structures import Meshes
from .app.utils import clean_up
from .app.custom_models.mvimg_prediction import run_mvprediction
from .app.custom_models.normal_prediction import predict_normals
from .scripts.refine_lr_to_sr import run_sr_fast
from .scripts.utils import save_glb_and_video
from .scripts.multiview_inference import geo_reconstruct
from .scripts.sd_model_zoo import load_common_sd15_pipe
from diffusers import StableDiffusionControlNetImg2ImgPipeline

import numpy as np


class Unique3DLoadPipeline:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ip_adapter": ([True, False],),
                "plus_model": ([True, False],),
            }
        }

    RETURN_TYPES = ("Unique3DPipeline",)
    RETURN_NAMES = ("pipe",)

    FUNCTION = "run"

    CATEGORY = "Unique3D"

    def run(self, ip_adapter, plus_model):
        base_model = "runwayml/stable-diffusion-v1-5"

        pipe = load_common_sd15_pipe(
            base_model=base_model, ip_adapter=ip_adapter, plus_model=plus_model,
            controlnet=f"{unique3d_path}/ckpt/controlnet-tile",
            pipeline_class=StableDiffusionControlNetImg2ImgPipeline)

        return (pipe,)


class Unique3DRun:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "pipe": ("Unique3DPipeline",),
                "input_processing": ([True, False],),
                "do_refine": ([True, False],),
                "render_video": ([True, False],),
                "predict_normal": ([True, False],),
                "init_type": (["std", "thin", "ball"],),
            },
        }

    RETURN_TYPES = ("IMAGE","STRING",)
    RETURN_NAMES = ("images","mesh_path",)

    FUNCTION = "run"

    CATEGORY = "Unique3D"

    def run(self, images, pipe, input_processing, do_refine, render_video, predict_normal, init_type):
        img_batch_np = images.cpu().detach().numpy().__mul__(255.).astype(np.uint8)

        preview_img = Image.fromarray(img_batch_np[0])

        if preview_img.size[0] <= 512:
            preview_img = run_sr_fast([preview_img])[0]

        seed = -1
        expansion_weight = 0.1

        rgb_pils, front_pil = run_mvprediction(preview_img, input_processing, int(seed))

        new_meshes, img_list, rm_normals = geo_reconstruct(
            pipe, rgb_pils, None, front_pil, do_refine=do_refine, predict_normal=predict_normal,
            expansion_weight=expansion_weight, init_type=init_type)

        vertices = new_meshes.verts_packed()
        vertices = vertices / 2 * 1.35
        vertices[..., [0, 2]] = - vertices[..., [0, 2]]
        new_meshes = Meshes(verts=[vertices], faces=new_meshes.faces_list(), textures=new_meshes.textures)

        output_folder = 'tmp/gradio'

        ret_mesh, video = save_glb_and_video(
            "/tmp/gradio/generated", new_meshes, with_timestamp=True, dist=3.5,
            fov_in_degrees=2 / 1.35, cam_type="ortho", export_video=render_video)



        return (images,ret_mesh,)


NODE_CLASS_MAPPINGS = {
    "Unique3DRun": Unique3DRun,
    "Unique3DLoadPipeline": Unique3DLoadPipeline
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Unique3DRun": Unique3DRun,
    "Unique3DLoadPipeline": Unique3DLoadPipeline
}
