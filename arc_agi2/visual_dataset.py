"""Readable episode bundles: lossless PNG, Python source and ImageFolder metadata.

One row = one episode with BOTH program and grid in its assistant completion.
The overview PNG includes the answer for human auditing; the text prompt does not.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

COLORS = ['#000000','#0074D9','#FF4136','#2ECC40','#FFDC00','#AAAAAA','#F012BE','#FF851B','#7FDBFF','#870C25']


def font(size):
    for name in ('/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(name).exists():return ImageFont.truetype(name,size)
    return ImageFont.load_default(size=size)


def render(record):
    pairs=[(f'Demonstration {i+1}',p['input'],p['output']) for i,p in enumerate(record['train'])]
    pairs += [(f'Query {i+1} · expected output',p['input'],a) for i,(p,a) in enumerate(zip(record['test'],record['solutions']))]
    cell=28
    column=max(440,max(len(g[0]) for _,a,b in pairs for g in (a,b))*cell)
    width=column*2+180
    heights=[max(len(a),len(b))*cell+108 for _,a,b in pairs]
    im=Image.new('RGB',(width,170+sum(heights)),'#101925');draw=ImageDraw.Draw(im)
    draw.text((36,22),'ARC · '+record['task_id'],font=font(30),fill='#f1f6ff')
    draw.text((36,65),record['episode_id'],font=font(20),fill='#aabdd5')
    draw.text((36,104),'INPUT',font=font(19),fill='#c4d5eb');draw.text((column+120,104),'OUTPUT',font=font(19),fill='#c4d5eb')
    y=140
    for (label,a,b),height in zip(pairs,heights):
        draw.rounded_rectangle((20,y,width-20,y+height-10),radius=12,fill='#142b32' if label.startswith('Query') else '#182332')
        draw.text((36,y+12),label,font=font(21),fill='#9be4c4')
        for left,g in [(36,a),(column+120,b)]:
            draw.text((left,y+43),f'{len(g)} × {len(g[0])}',font=font(18),fill='#abbcd2')
            gx=left+(column-len(g[0])*cell)//2;gy=y+73
            for rr,row in enumerate(g):
                for cc,c in enumerate(row):
                    x0,y0=gx+cc*cell,gy+rr*cell
                    draw.rectangle((x0,y0,x0+cell-2,y0+cell-2),fill=COLORS[c])
        y+=height
    return im


def write_bundle(record, output):
    output=Path(output);tid=record['task_id'];eid=record['episode_id']
    folder=output/'episodes'/tid;folder.mkdir(parents=True,exist_ok=True)
    image=folder/(eid+'.png');render(record).save(image,format='PNG',optimize=True)
    programs=output/'programs'/tid;programs.mkdir(parents=True,exist_ok=True)
    program=programs/(record['program_sha256']+'.py');program.write_text(record['program'])
    # ImageFolder converts file_name into an Image feature in the HF viewer.
    meta={'file_name':image.name,'episode_id':eid,'task_id':tid,'program':record['program'],
          'output_grid':record['output_json'],'prompt':record['prompt'],'completion':record['completion'],
          'program_file':str(program.relative_to(output)),
          'verification':'All demonstration and query grids exact',
          'source_revision':record['source_revision'],'solver_basis':record['solver_basis'],
          'image_usage':'Human audit overview includes the answer; use prompt for model input.'}
    with (folder/'metadata.jsonl').open('a') as f:f.write(json.dumps(meta,separators=(',',':'))+'\n')
    return str(image.relative_to(output))
