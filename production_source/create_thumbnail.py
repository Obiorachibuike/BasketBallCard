#!/usr/bin/env python3
"""Typeset the thumbnail on a generated scene image."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
out=ROOT.parent/'deliverables'; out.mkdir(exist_ok=True)
im=ImageOps.fit(Image.open(ROOT/'shots'/'10_mind.jpg').convert('RGB'),(1280,720),method=Image.Resampling.LANCZOS)
veil=Image.new('RGBA',im.size,(0,0,0,0)); d=ImageDraw.Draw(veil)
for y in range(405,720):
    z=(y-405)/315; d.line((0,y,1280,y),fill=(0,5,12,int(232*z**1.1)))
im=Image.alpha_composite(im.convert('RGBA'),veil); d=ImageDraw.Draw(im)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; f1=ImageFont.truetype(font,77); f2=ImageFont.truetype(font,92)
d.rounded_rectangle((52,466,62,677),radius=4,fill=(80,224,255,255))
d.text((83,482),'CAN YOU',font=f1,anchor='lt',fill='white',stroke_width=3,stroke_fill=(0,8,18,255))
d.text((83,571),'LIVE FOREVER?',font=f2,anchor='lt',fill=(167,239,255,255),stroke_width=4,stroke_fill=(0,8,18,255))
im.convert('RGB').save(out/'AI_Uncovered_Thumbnail.jpg',quality=94,optimize=True,subsampling=0)
print('Created 1280x720 thumbnail')
