#!/bin/bash

/bin/bash -c 'cd /usr/local/minigpt4 && source /usr/local/miniconda/bin/activate minigpt4 && uvicorn main:app --host 0.0.0.0 --port 8000'