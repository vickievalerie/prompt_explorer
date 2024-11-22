import json
import os
from ycloud import *
from hsecloud import *
import functools as funt
import time
import uuid

output_dir = '../samples'

with open('description-ya.json',encoding='utf-8') as f:
    desc = json.load(f)

models = {
    'YA' : ("Yandex ART","_ru",submit_art,check),
    'sd2' : ("Stable Diffusion 2","",funt.partial(submit_hse,model="sd2"),check_hse),
    'sdxl' : ("Stable Diffusion XL","",funt.partial(submit_hse,model="sdxl"),check_hse),
    'k22' : ("Kandinsky 2","",funt.partial(submit_hse,model="k22"),check_hse),
    'flux' : ("Flux","",None,None),
    'k3' : ("Kandinsky 3","",None,None),
}

jobs = []
metaindex = {}
for obj in desc:
    cat = obj['category']
    title = obj['title']
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
            if i>0:
                skip += 1
            else:
                if submit_fn:
                    id = submit_fn(p)
                else:
                    id = uuid.uuid4()
                    jobs.append({ "model" : m, "prompt" : p, "fname" : os.path.join(dir,fname) })
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
            if fun is None:
                queue[id] = None
                items[mname][p] = [fname.format(0)]
                continue
            if res:=fun(id):
                for i,im in enumerate(res):
                    im.save(os.path.join(output_dir,dir,fname.format(i)))
                    items[mname][p] = items[mname].get(p,[]) + [fname.format(i)]
                print('.',end='',flush=True)
                queue[id] = None
    print("..done")
    with open('jobs.json','w',encoding='utf-8') as f:
        json.dump(jobs,f)
    print(" + Generating markdown")
    metaindex[os.path.join(dir,'index.md')] = dir 
    with open(os.path.join(output_dir,dir,'index.md'),'a',encoding='utf-8') as f:
        f.write(f"## {title} ({cat})\n\n")
        for mname, v in items.items():
            f.write(f"### {mname}\n\n")
            l = list(v.values()) 
            for i in range(len(l[0])):
                f.write(' | '.join([f"[![]({x[i]})]({x[i]})" for x in l])+'\n')
                if i==0:
                    f.write('|'.join(['-----']*len(v.values()))+'\n')
            f.write(' | '.join(v.keys())+'\n\n')
print(" + Saving metaindex")
with open(os.path.join(output_dir,'metaindex.md'),'w',encoding='utf-8') as f:
    f.write(f'## Metaindex\n\n')
    for p,t in metaindex.items():
        z = p.replace('\\','/')
        f.write(f" * [{t}]({z})\n")
print(" + Done")

