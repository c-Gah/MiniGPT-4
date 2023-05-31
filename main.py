import os
import random

import numpy as np
import torch
import torch.backends.cudnn as cudnn

from fastapi import FastAPI, Request, File, Form, UploadFile
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
import io


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

cfg_path = "eval_configs/minigpt4_eval.yaml"  # replace with your actual path
gpu_id = 0  # replace with your actual GPU ID
options = ['option1=value1', 'option2=value2']  # replace with your actual options

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

# ========================================
#             Supporting Functions
# ========================================

def check_cuda_memory():
    # Ensure that a CUDA device is available
    if torch.cuda.is_available():
        # Get current device (GPU)
        device = torch.cuda.current_device()
        
        # Get current memory allocation and total memory (in bytes)
        current_memory = torch.cuda.memory_allocated(device)
        max_memory = torch.cuda.max_memory_allocated(device)

        # Convert bytes to gigabytes
        current_memory_gb = current_memory / (1024 ** 3)
        max_memory_gb = max_memory / (1024 ** 3)

        # Compute memory usage percentage
        memory_usage_percentage = (current_memory / max_memory) * 100

        print(f'Current memory usage: {current_memory_gb} GB')
        print(f'Max memory usage: {max_memory_gb} GB')
        print(f'Memory usage percentage: {memory_usage_percentage}%')

        if memory_usage_percentage >= 90:
            print('Memory usage is more than 90%. Exiting...')
            exit(0)
    else:
        print('CUDA is not available on this machine')

# ========================================
#             FastAPI Setting
# ========================================
@app.get("/hello")
async def hello_world():
    return {"message": "Hello, World!"}
    
    
@app.post("/upload_ask_answer")
async def upload_ask_answer(file: UploadFile = File(...), question: str = Form(...)):
    # check_cuda_memory()

    # Read image file
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    # Image Processing
    chat_state = CONV_VISION.copy()
    img_list = []
    llm_message = chat.upload_img(image, chat_state, img_list)

    # Ask
    chat.ask(question, chat_state)
    
    # Answer
    answer = chat.answer(conv=chat_state,
                              img_list=img_list,
                              num_beams=5,
                              temperature=1.0,
                              max_new_tokens=300,
                              max_length=2000)[0]

    # Reset GPU memory
    torch.cuda.empty_cache()

    # Return response
    return {"answer": answer}
