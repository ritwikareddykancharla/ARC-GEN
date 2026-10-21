"""Individual PNG images and one compact ImageFolder metadata record per episode.

No archives or binary viewer indexes. A public export contains only PNG and text.
"""
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
from PIL import Image, ImageDraw, ImageColor
from .visual_dataset import COLORS, font

PALETTE = COLORS + ['#101925','#f1f6ff','#aabdd5','#c4d5eb','#142b32','#182332','#9be4c4','#abbcd2']

def render_png(record, pixel_ratio=1):
    """Render directly at the requested pixel density, never upscale raster text."""
    if not isinstance(pixel_ratio, int) or not 1 <= pixel_ratio <= 4:
        raise ValueError('pixel_ratio must be an integer from 1 to 4')
    pairs=[(f'Demonstration {i+1}',p['input'],p['output']) for i,p in enumerate(record['train'])]
    pairs += [(f'Query {i+1} - expected output',p['input'],a) for i,(p,a) in enumerate(zip(record['test'],record['solutions']))]
    cell=28;column=max(440,max(len(g[0]) for _,a,b in pairs for g in (a,b))*cell)
    width=column*2+180;heights=[max(len(a),len(b))*cell+108 for _,a,b in pairs]
    scale=pixel_ratio
    im=Image.new('RGB',(width*scale,(170+sum(heights))*scale),PALETTE[10])
    draw=ImageDraw.Draw(im);draw.fontmode='L'
    def text(x,y,label,size,colour):
        draw.text((x*scale,y*scale),label,font=font(size*scale),fill=PALETTE[colour])
    # Original logical font sizes; density changes sharpness, not label size.
    text(36,22,'ARC - '+record['task_id'],30,11)
    text(36,65,record['episode_id'],20,12)
    text(36,104,'INPUT',19,13);text(column+120,104,'OUTPUT',19,13)
    y=140
    for (label,a,b),height in zip(pairs,heights):
        draw.rounded_rectangle(tuple(v*scale for v in (20,y,width-20,y+height-10)),radius=12*scale,fill=PALETTE[14] if label.startswith('Query') else PALETTE[15])
        text(36,y+12,label,21,16)
        for left,g in [(36,a),(column+120,b)]:
            text(left,y+43,f'{len(g)} x {len(g[0])}',18,17)
            gx=left+(column-len(g[0])*cell)//2;gy=y+73
            for rr,row in enumerate(g):
                for cc,c in enumerate(row):
                    x0,y0=gx+cc*cell,gy+rr*cell
                    # Preserve the exact logical cell footprint at every density.
                    draw.rectangle((x0*scale,y0*scale,(x0+cell-1)*scale-1,(y0+cell-1)*scale-1),fill=COLORS[c])
        y+=height
    return im

class PNGDirectoryWriter:
    def __init__(self,directory,family,max_records=1000,**unused):
        if not re.fullmatch('[0-9a-f]{8}',family):raise ValueError('Invalid family')
        self.directory=Path(directory)/family
        self.family=family;self.max_records=max_records;self.records=0
        self.paths=[];self.manifest=[];self.seen=set();self.stream=None;self.bucket=None
    def _finish(self):
        if self.stream is None:return
        self.stream.close();self.stream=None
        meta=self.bucket/'metadata.jsonl'
        (self.bucket/'metadata.jsonl.tmp').replace(meta)
        self.paths.append(meta)
        self.manifest.append({'file':str(meta.relative_to(self.directory.parent)),
            'episodes':self.bucket_records,'png_bytes':self.bucket_bytes,
            'metadata_sha256':hashlib.sha256(meta.read_bytes()).hexdigest(),'format':'individual-png'})
        print(json.dumps({'stage':'png_folder_complete','family':self.family,'pngs':self.records,'folder':str(self.bucket),'png_bytes':self.bucket_bytes}),flush=True)
        self.bucket=None
    def write(self,record):
        if not record.get('verification',{}).get('all_exact'):raise ValueError('Unverified episode')
        eid=record['episode_id']
        if not re.fullmatch('[A-Za-z0-9_-]+',eid) or eid in self.seen:raise ValueError('Invalid or duplicate episode ID')
        if record['task_id']!=self.family:raise ValueError('Wrong family')
        if len(record['train'])!=3 or len(record['test'])!=len(record['solutions']):raise ValueError('Invalid episode layout')
        program=record['program']
        if hashlib.sha256(program.encode()).hexdigest()!=record['program_sha256']:raise ValueError('Program hash mismatch')
        if json.loads(record['output_json'])!={'outputs':record['solutions']}:raise ValueError('Grid target mismatch')
        im=render_png(record);data=io.BytesIO();im.save(data,format='PNG',compress_level=6);payload=data.getvalue()
        # Verify the encoded pixels, including colour indices, before admission.
        with Image.open(io.BytesIO(payload)) as decoded:
            decoded.load()
            if decoded.size!=im.size or decoded.tobytes()!=im.tobytes() or decoded.getpalette()!=im.getpalette():raise ValueError('PNG pixel mismatch')
        if self.stream is None:
            self.bucket=self.directory/f'{len(self.manifest):05d}'
            self.bucket.mkdir(parents=True,exist_ok=False)
            self.stream=(self.bucket/'metadata.jsonl.tmp').open('w');self.bucket_records=0;self.bucket_bytes=0
        path=self.bucket/(eid+'.png');path.write_bytes(payload)
        # Store grids and source once. Prompt/completion are derived at training load.
        excluded={'prompt','completion','messages','output_json','source_episode_id','program'}
        provenance={k:v for k,v in record.items() if k not in excluded and k not in ('train','test','solutions')}
        meta={'file_name':path.name,'episode_id':eid,'task_id':self.family,
              'program':program,'challenge_json':json.dumps({'train':record['train'],'test':record['test']},separators=(',',':')),
              'answer_json':record['output_json'],'provenance_json':json.dumps(provenance,separators=(',',':')),
              'png_sha256':hashlib.sha256(payload).hexdigest(),
              'image_usage':'Human audit image includes query answers. Train using challenge_json and program/answer_json only.'}
        self.stream.write(json.dumps(meta,separators=(',',':'))+'\n')
        self.seen.add(eid);self.records+=1;self.bucket_records+=1;self.bucket_bytes+=len(payload)
        if self.bucket_records>=self.max_records:self._finish()
    def close(self):self._finish()
    def abort(self):
        if self.stream:self.stream.close();self.stream=None
        if self.directory.exists():shutil.rmtree(self.directory)
        self.paths=[];self.manifest=[]
