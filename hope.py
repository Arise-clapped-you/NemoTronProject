import os
import sys
import requests
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
import json
import base64
import cv2
import numpy as np
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
connected_pis = {}

invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
query = "Describe the image in detail"
kApiKey = "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"
stream = True

media_samples = list()

@app.get("/")
def home():
    return HTMLResponse("<h2>Coordinator running!</h2>")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    init = await websocket.receive_text()
    init_data = json.loads(init)
    node = init_data.get("node")
    connected_pis[node] = websocket
    print(f"{node} connected")

    imgCount = 0
    content = [{"type": "text", "text": query}]
    try:
        
        while True: #imgCount < 5:
            data = await websocket.receive_text()
            
                        

 
            mgCount += 1
            media_obj = {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{"image/jpeg"};base64,{data}"
                        }
                    }
            content.append(media_obj)

             

            if imgCount >= 5:
                headers = {
                            "Authorization": f"Bearer {kApiKey}",
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        }

                system_prompt = "/think"

                messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": content},
                        ]

                payload = {
                            "max_tokens": 4096,
                            "temperature": 1,
                            "top_p": 1,
                            "frequency_penalty": 0,
                            "presence_penalty": 0,
                            "messages": messages,
                            "stream": stream,
                            "model": "nvidia/nemotron-nano-12b-v2-vl",
                        }
                print("\nSending request to NVIDIA API...\n")
                response = requests.post(invoke_url, headers=headers, json=payload, stream=stream)
                data = response.json()

                full_response = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(full_response)

                imgCount = 0
                content = [{"type": "text", "text": query}]
                # print(response)

    except Exception as e:
        print(f"{node} disconnected: {e}")
    finally:
        connected_pis.pop(node, None)
        cv2.destroyAllWindows()


# Run with: uvicorn hope:app --host 0.0.0.0 --port 8000
