import requests
import os
import json
import io
from PIL import Image
import base64

config = json.load(open("config.json"))

def call_api(url, data):
    headers = { "Authorization" : f"Api-Key {config['api_key']}" }
    return requests.post(url, json=data, headers=headers).json()

def call_api_get(url):
    headers = { "Authorization" : f"Api-Key {config['api_key']}" }
    return requests.get(url, headers=headers).json()

def submit_art(prompt):
    res = call_api("https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync",
    {
        "modelUri": f"art://{config['folder_id']}/yandex-art/latest",
        "messages": [
          {
            "weight": 1,
            "text": prompt
          }
        ]
    })
    if 'error' in res:
        print(res)
        return None
    return res['id']


def decode_image(base64_str):
    return Image.open(io.BytesIO(base64.decodebytes(bytes(base64_str, "utf-8"))))

def check(id):
    res = call_api_get(f"https://llm.api.cloud.yandex.net:443/operations/{id}")
    if 'done' in res and res['done']:
        return [decode_image(res['response']['image'])]
    else:
        return None
