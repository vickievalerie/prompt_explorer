import json
import os
from ycloud import *
from hsecloud import *
import functools as funt
import time

output_dir = '../samples'
skip_if_exists = True

with open('description.json',encoding='utf-8') as f:
    desc = json.load(f)

models = {
    'YA' : ("Yandex ART","_ru",submit_art,check),
    'sdxl' : ("Stable Diffusion XL","",funt.partial(submit_hse,model="sdxl"),check_hse),
    'k22' : ("Kandinsky","",funt.partial(submit_hse,model="k22"),check_hse),
}

for obj in desc:
    cat = obj['category']
    dir = cat[:cat.rfind('/')]
    cat = cat[cat.rfind('/')+1:]
    print(f" + Processing category {dir} -> {cat}")
    os.makedirs(os.path.join(output_dir,dir),exist_ok=True)
    queue = {}
    items = {}
    for m in models.keys():
        mname, lang, submit_fn, check_fn = models[m]
        items[mname] = { }
        prompt = obj[f"prompt{lang}"]
        values = obj[f"values{lang}"]
        print(f" + Submitting for model {m}..",end='',flush=True)
        sub,skip = 0,0
        for v in values:
            p = prompt.format(v)
            # preload existing images
            i = 0
            while True:
                fname = f"{m}_{p.replace(' ','_')}_{i}.png"
                if not os.path.exists(os.path.join(output_dir,dir,fname)):
                    break
                items[mname][p] = items[mname].get(p,[]) + [fname]
                i+=1
            if i>0 and skip_if_exists:
                skip += 1
            else:
                id = submit_fn(p)
                sub += 1
                queue[id] = (check_fn,f"{m}_{p.replace(' ','_')}_{{}}.png",mname,p)
        print(f'{sub} submitted, {skip} skipped')
    print(" + Checking ",end='',flush=True)
    while True:
        time.sleep(2)
        queue = { k:v for k,v in queue.items() if v is not None }
        if len(queue) == 0:
            break
        for id,(fun,fname,mname,p) in queue.items(): 
            if res:=fun(id):
                for i,im in enumerate(res):
                    im.save(os.path.join(output_dir,dir,fname.format(i)))
                    items[mname][p] = items[mname].get(p,[]) + [fname.format(i)]
                print('.',end='',flush=True)
                queue[id] = None
    print("..done")
    print(" + Generating markdown")
    with open(os.path.join(output_dir,dir,'index.md'),'w',encoding='utf-8') as f:
        f.write(f"## {cat}\n\n")
        for mname, v in items.items():
            f.write(f"### {mname}\n\n")
            l = list(v.values()) 
            for i in range(len(l[0])):
                f.write(' | '.join([f"![]({x[i]})" for x in l])+'\n')
                if i==0:
                    f.write('|'.join(['-----']*len(l[0]))+'\n')
            f.write(' | '.join(v.keys())+'\n\n')
