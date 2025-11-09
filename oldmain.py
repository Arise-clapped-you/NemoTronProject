import requests
import os
import base64
import sys
import json
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio, json, base64, cv2, numpy as np

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    init = await websocket.receive_text()
    init_data = json.loads(init)
    node = init_data.get("node")
    

# NVIDIA API endpoint
invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"

# Stream output in real-time
stream = True
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)
# Default user query
query = "Describe the image in detail"

# Your API Key (set via environment variable in production)
kApiKey = "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"

# Supported file types
kSupportedList = {
    "png": ["image/png", "image_url"],
    "base64_data": ["image/jpeg", "image_url"],
    "jpeg": ["image/jpeg", "image_url"],
    "webp": ["image/webp", "image_url"],
    "mp4": ["video/mp4", "video_url"],
    "webm": ["video/webm", "video_url"],
    "mov": ["video/mov", "video_url"]
}


def get_extension(filename):
    _, ext = os.path.splitext(filename)
    return ext[1:].lower()


def mime_type(ext):
    return kSupportedList[ext][0]


def media_type(ext):
    return kSupportedList[ext][1]


def encode_media_base64(media_file):
    """Encode media file to base64 string"""
    with open(media_file, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def chat_with_media(infer_url, media_files, query: str, stream: bool = False):
    """Sends image/video/text to NVIDIA API and collects response text"""
    has_video = False
    full_response = ""  # 👈 variable to collect the streamed response

    # Build content array
    if len(media_files) == 0:
        content = query
    else:
        content = [{"type": "text", "text": query}]
        for media_file in media_files:
            ext = get_extension(media_file)
            assert ext in kSupportedList, f"{media_file} format is not supported"
            media_type_key = media_type(ext)

            if media_type_key == "video_url":
                has_video = True

            print(f"Encoding {media_file} as base64...")
            base64_data = encode_media_base64(media_file)

            media_obj = {
                "type": media_type_key,
                media_type_key: {
                    "url": f"data:{mime_type(ext)};base64,{base64_data}"
                }
            }
            content.append(media_obj)

        if has_video:
            assert len(media_files) == 1, "Only single video supported."

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {kApiKey}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if stream:
        headers["Accept"] = "text/event-stream"

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

    response = requests.post(infer_url, headers=headers, json=payload, stream=stream)

    if stream:
        print("Response:\n")
        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data = line[len("data: "):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        parsed = json.loads(data)
                        content_piece = parsed["choices"][0]["delta"].get("content", "")
                        full_response += str(content_piece)  # 👈 collect text
                        print(content_piece, end="", flush=True)
                    except json.JSONDecodeError:
                        pass

        print("\n\n✅ Done.")
    else:
        data = response.json()
        full_response = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(full_response)

    return full_response  # 👈 return the collected response text


if __name__ == "__main__":  
    """
    Usage:
        python test_nvidia.py sample.jpg
        python test_nvidia.py sample.mp4
    """
    media_samples = list(sys.argv[1:])
    
    result = chat_with_media(invoke_url, media_samples, query, stream)
    print("\n\n🧠 Final Collected Response:\n", result)
    
@app.get("/get-string")
def get_string():
    return {"message": "Hello from FastAPI!"}