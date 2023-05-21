import os
import random

import numpy as np
import torch
import torch.backends.cudnn as cudnn

from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from minigpt4.common.config import Config
from minigpt4.common.dist_utils import get_rank
from minigpt4.common.registry import registry
from minigpt4.conversation.conversation import Chat, CONV_VISION

# imports modules for registration
from minigpt4.datasets.builders import *
from minigpt4.models import *
from minigpt4.processors import *
from minigpt4.runners import *
from minigpt4.tasks import *

from PIL import Image

from io import BytesIO

import torchvision.transforms as transforms


def setup_seeds(config):
    seed = config.run_cfg.seed + get_rank()

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    cudnn.benchmark = False
    cudnn.deterministic = True


# ========================================
#             Model Initialization
# ========================================

print('Initializing Chat')
# Hardcoding the values directly
cfg_path = "eval_configs/minigpt4_eval.yaml"  # replace with your actual path
gpu_id = 0  # replace with your actual GPU ID
options = ['option1=value1', 'option2=value2']  # replace with your actual options

# Create a new class to mimic the argparse Namespace
class Args:
    def __init__(self, cfg_path, gpu_id, options):
        self.cfg_path = cfg_path
        self.gpu_id = gpu_id
        self.options = options

args = Args(cfg_path, gpu_id, options)

cfg = Config(args)

model_config = cfg.model_cfg
model_config.device_8bit = args.gpu_id
model_cls = registry.get_model_class(model_config.arch)
model = model_cls.from_config(model_config).to('cuda:{}'.format(args.gpu_id))

vis_processor_cfg = cfg.datasets_cfg.cc_sbu_align.vis_processor.train
vis_processor = registry.get_processor_class(vis_processor_cfg.name).from_config(vis_processor_cfg)
chat = Chat(model, vis_processor, device='cuda:{}'.format(args.gpu_id))
print('Initialization Finished')


app = FastAPI()
templates = Jinja2Templates(directory="templates")

origins = [
    "*",  # Allow all origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/hello")
async def hello_world():
    return {"message": "Hello, World 3!"}
    
@app.post("/upload_img/")
async def upload_img(request: Request, file: UploadFile = File(...)):
    gr_img = await file.read() # You should convert this to required format.
    if gr_img is None:
        return {"status": "failure", "reason": "No image uploaded"}
        
    chat_state = CONV_VISION.copy()
    img_list = []
    llm_message = chat.upload_img(gr_img, chat_state, img_list)
    return {"status": "success", "message": llm_message}

@app.post("/upload_img2/")
async def upload_img2(request: Request, file: UploadFile = File(...)):
    print('11111111')
    gr_img = await file.read()
    if gr_img is None:
        return {"status": "failure", "reason": "No image uploaded"}
    
    # Convert bytes to PIL image
    img_pil = Image.open(BytesIO(gr_img))

    # Apply necessary transformations: resize, normalize, etc.
    # assuming you want to convert to a tensor and normalize to the range [0, 1]
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # adjust size if necessary
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # adjust normalization if necessary
    ])

    img_tensor = transform(img_pil).unsqueeze(0)  # add batch dimension

    chat_state = CONV_VISION.copy()
    img_list = []
    llm_message = chat.upload_img(img_tensor, chat_state, img_list)
    return {"status": "success", "message": llm_message}


@app.post("/ask/")
def ask(request: Request, user_message: str):
    if len(user_message) == 0:
        return {"status": "failure", "reason": "Input should not be empty!"}
    chat_state = request.session.get("chat_state", None)
    chat.ask(user_message, chat_state)
    request.session["chat_state"] = chat_state
    return {"status": "success"}

@app.post("/answer/")
def answer(request: Request, num_beams: int, temperature: float):
    chat_state = request.session.get("chat_state", None)
    img_list = request.session.get("img_list", [])
    llm_message = chat.answer(conv=chat_state,
                              img_list=img_list,
                              num_beams=num_beams,
                              temperature=temperature,
                              max_new_tokens=300,
                              max_length=2000)[0]
    return {"status": "success", "message": llm_message}

@app.post("/reset/")
def reset(request: Request):
    request.session["chat_state"] = None
    request.session["img_list"] = []
    torch.cuda.empty_cache()
    return {"status": "success"}