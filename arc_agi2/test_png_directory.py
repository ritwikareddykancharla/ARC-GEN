import tempfile,json,hashlib,unittest
from pathlib import Path
from PIL import Image,ImageColor
from .png_directory import PNGDirectoryWriter,COLORS
from .program_targets import make_record,verify
from . import test_program_targets as fixtures

class DirectPNGs(unittest.TestCase):
 def test_pixels_metadata_targets_and_no_binary_containers(self):
  with tempfile.TemporaryDirectory() as d:
   w=PNGDirectoryWriter(d,'00dbd492',max_records=1)
   for i in range(2):
    ep=fixtures.ProgramTargets().episode('00dbd492',i);ep['episode_id']+=f'-{i}';ep['train']=ep['train'][:3]
    r=make_record(ep);w.write(r)
   w.close();self.assertEqual(w.records,2)
   self.assertEqual(len(list(Path(d).rglob('*.png'))),2)
   self.assertTrue(all(p.suffix in ('.png','.jsonl') for p in Path(d).rglob('*') if p.is_file()))
   for p in w.paths:
    row=json.loads(p.read_text());challenge=json.loads(row['challenge_json']);answers=json.loads(row['answer_json'])['outputs']
    self.assertTrue(verify(row['program'],{**challenge,'solutions':answers})['all_exact'])
    im=Image.open(p.parent/row['file_name']).convert('RGB')
    a=challenge['train'][0]['input'];column=max(440,max(len(g[0]) for pair in challenge['train'] for g in pair.values())*28,max(len(x['input'][0])*28 for x in challenge['test']),max(len(x[0])*28 for x in answers))
    gx=36+(column-len(a[0])*28)//2
    for y,rr in enumerate(a):
     for x,c in enumerate(rr):self.assertEqual(im.getpixel((gx+x*28+5,213+y*28+5)),ImageColor.getrgb(COLORS[c]))
    self.assertNotIn('prompt',row);self.assertNotIn('completion',row)
    self.assertEqual(hashlib.sha256((p.parent/row['file_name']).read_bytes()).hexdigest(),row['png_sha256'])
 def test_reject_and_abort(self):
  with tempfile.TemporaryDirectory() as d:
   w=PNGDirectoryWriter(d,'00dbd492');ep=fixtures.ProgramTargets().episode('00dbd492');ep['train']=ep['train'][:3];r=make_record(ep)
   with self.assertRaises(ValueError):w.write(dict(r,verification={'all_exact':False}))
   w.write(r)
   with self.assertRaises(ValueError):w.write(r)
   w.abort();self.assertFalse(list(Path(d).rglob('*.png')))
if __name__=='__main__':unittest.main()
