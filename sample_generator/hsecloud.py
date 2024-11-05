import requests
from PIL import Image
from io import BytesIO

def submit_hse(prompt,model='sdxl'):
    j = {
        'prompt' : prompt
    }
    res = requests.post(f'https://new.dmin.pro/dreaim/submit/{model}', json=j)
    return res.json()['id']

def check_hse(id):
    res = requests.get(f'https://new.dmin.pro/dreaim/check/{id}').json()
    if res['status'] != 'ok':
        return None
    seeds = res['seeds']
    imgs = [ requests.get(f'https://new.dmin.pro/dreaim/get/{id}/{x}').content for x in seeds]
    return [Image.open(BytesIO(x)) for x in imgs]
