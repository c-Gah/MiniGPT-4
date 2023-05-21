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

# ========================================
#          Eviorment Initialization
# ========================================
#export CFG_PATH="/path/to/config"
#export GPU_ID="0"

# ========================================
#             Model Initialization
# ========================================

print('Initializing Chat')
# cfg_path = os.getenv("CFG_PATH")
cfg_path = "eval_configs/minigpt4_eval.yaml"
# gpu_id = int(os.getenv("GPU_ID", "0"))
gpu_id = 0
# These are the hardcoded options, replace with your own values

class Args:
    def __init__(self, cfg_path, gpu_id, options):
        self.cfg_path = cfg_path
        self.gpu_id = gpu_id
        self.options = options

# These are the hardcoded options, replace with your own values
options = ["option1=value1", "option2=value2", "option3=value3"]
args = Args(cfg_path='eval_configs/minigpt4_eval.yaml', gpu_id=0, options=options)

cfg = Config(args)


model_config = cfg.model_cfg
model_config.device_8bit = gpu_id
model_cls = registry.get_model_class(model_config.arch)
model = model_cls.from_config(model_config).to('cuda:{}'.format(gpu_id))

vis_processor_cfg = cfg.datasets_cfg.cc_sbu_align.vis_processor.train
vis_processor = registry.get_processor_class(vis_processor_cfg.name).from_config(vis_processor_cfg)
chat = Chat(model, vis_processor, device='cuda:{}'.format(gpu_id))
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
    return {"status": "success"}

