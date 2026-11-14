#!/usr/bin/env python3
"""Generate original animated scientific motion graphics."""
from __future__ import annotations
import math
import subprocess
from pathlib import Path
import imageio_ffmpeg
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'graphics'; OUT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe(); W,H=960,540; FPS=24; DURATION=16
FNT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
BOLD=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
SMALL=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)

def writer(filename):
    return subprocess.Popen([FF,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
        '-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','19',
        '-pix_fmt','yuv420p','-threads','2','-movflags','+faststart',str(OUT/filename)],stdin=subprocess.PIPE)

def finish(proc):
    proc.stdin.close()
    if proc.wait(): raise RuntimeError('graphics encoder failed')

def background():
    y,x=np.mgrid[0:H,0:W]; r=np.sqrt(((x-W*.5)/(W*.8))**2+((y-H*.5)/(H*.8))**2)
    a=np.empty((H,W,3),np.uint8); a[:,:,0]=np.clip(5-4*r,1,5); a[:,:,1]=np.clip(19-16*r,4,19); a[:,:,2]=np.clip(31-22*r,9,31)
    return Image.fromarray(a,'RGB')

def network():
    rng=np.random.default_rng(54); coords=[]
    while len(coords)<520:
        x,y,z=rng.uniform(-1,1,3)
        if x*x+y*y+z*z>1: continue
        side=-1 if len(coords)%2 else 1; coords.append((side*.39+x*.44,y*.74,z*.57))
    pts=np.array(coords); neighbors=cKDTree(pts).query(pts,k=4)[1]
    edges=sorted({tuple(sorted((i,int(j)))) for i,row in enumerate(neighbors) for j in row[1:] if i!=j})
    pulse_edges=rng.choice(len(edges),size=55,replace=False); phases=rng.uniform(0,1,len(pulse_edges))
    stars=rng.uniform([15,15],[W-15,H-15],(105,2)); base=background(); proc=writer('network.mp4')
    for frame in range(DURATION*FPS):
        t=frame/FPS; img=base.copy(); d=ImageDraw.Draw(img,'RGBA')
        for k,(x,y) in enumerate(stars):
            a=int(25+25*(1+math.sin(t*.8+k))*.5); d.ellipse((x,y,x+1.4,y+1.4),fill=(91,166,200,a))
        yaw=t*.16; tilt=.13+math.sin(t*.19)*.05
        ry=np.array([[math.cos(yaw),0,math.sin(yaw)],[0,1,0],[-math.sin(yaw),0,math.cos(yaw)]])
        rx=np.array([[1,0,0],[0,math.cos(tilt),-math.sin(tilt)],[0,math.sin(tilt),math.cos(tilt)]])
        p=pts@(ry@rx).T; perspective=1/(1-.22*p[:,2]); sx=W*.5+p[:,0]*330*perspective; sy=H*.51+p[:,1]*268*perspective
        for a,b in edges:
            depth=(p[a,2]+p[b,2])*.5; alpha=int(35+max(0,depth+.6)*45)
            d.line((sx[a],sy[a],sx[b],sy[b]),fill=(44,153,200,min(105,alpha)),width=1)
        for ix in np.argsort(p[:,2]):
            pulse=.5+.5*math.sin(t*1.8+ix*.72); rad=1.3+max(0,p[ix,2]+.2); a=int(80+130*pulse)
            d.ellipse((sx[ix]-rad,sy[ix]-rad,sx[ix]+rad,sy[ix]+rad),fill=(120,225,255,a))
        for n,eidx in enumerate(pulse_edges):
            a,b=edges[eidx]; q=(t*.23+phases[n])%1; px=sx[a]*(1-q)+sx[b]*q; py=sy[a]*(1-q)+sy[b]*q
            d.ellipse((px-2,py-2,px+2,py+2),fill=(195,247,255,230))
        d.text((42,34),'NEURAL NETWORK',font=BOLD,fill=(153,231,255,220))
        d.text((42,60),'CONCEPTUAL VISUALIZATION  /  NOT ACTUAL BRAIN DATA',font=SMALL,fill=(131,177,194,180))
        proc.stdin.write(img.tobytes())
    finish(proc); print('created 3D neural network graphic',flush=True)

def bci():
    base=background(); proc=writer('bci.mp4')
    for frame in range(DURATION*FPS):
        t=frame/FPS; img=base.copy(); d=ImageDraw.Draw(img,'RGBA')
        d.text((45,31),'BRAIN-COMPUTER INTERFACE',font=BOLD,fill=(171,238,255,235))
        d.text((45,59),'CONCEPTUAL DEMONSTRATION  /  SIMULATED SIGNALS',font=SMALL,fill=(126,177,196,185))
        d.rounded_rectangle((43,105,575,438),radius=12,outline=(53,140,167,185),width=2,fill=(5,25,38,215))
        d.rounded_rectangle((606,105,918,438),radius=12,outline=(53,140,167,185),width=2,fill=(5,25,38,215))
        d.text((65,126),'ELECTRODE SIGNALS',font=FNT,fill=(179,222,234,225))
        d.text((629,126),'CURSOR CONTROL',font=FNT,fill=(179,222,234,225))
        for row in range(4):
            cy=196+row*61
            for xx in range(76,550,50): d.line((xx,cy-20,xx,cy+20),fill=(34,68,83,80),width=1)
            d.line((74,cy,550,cy),fill=(45,92,108,110),width=1); arr=[]
            for x in range(76,551,2):
                q=x*.043-t*3.5+row*1.2; amp=8*math.sin(q)+4*math.sin(q*2.7+1.5)+3*math.sin(q*.37+row)
                spike=10*math.sin(q*.7)*max(0,math.sin(q*.21-1.5))**8; arr.append((x,cy+amp+spike))
            d.line(arr,fill=(55,200,229,210),width=2)
        tx=760+75*math.sin(t*.52); ty=270+65*math.sin(t*.39+.6)
        for r,alpha in [(42,35),(26,75),(12,160)]: d.ellipse((tx-r,ty-r,tx+r,ty+r),outline=(71,210,239,alpha),width=2)
        px=tx+24; py=ty+15
        d.polygon([(px,py),(px,py+37),(px+10,py+29),(px+18,py+45),(px+24,py+42),(px+16,py+26),(px+30,py+24)],fill=(216,251,255,235))
        d.text((632,390),'DECODED CONTROL',font=SMALL,fill=(126,177,196,185)); proc.stdin.write(img.tobytes())
    finish(proc); print('created BCI graphic',flush=True)

def particles():
    rng=np.random.default_rng(93); x=rng.uniform(0,W,75); y=rng.uniform(0,H,75)
    speed=rng.uniform(2,10,75); phase=rng.uniform(0,6.28,75); proc=writer('particles.mp4')
    for frame in range(DURATION*FPS):
        t=frame/FPS; img=Image.new('RGB',(W,H),(0,0,0)); d=ImageDraw.Draw(img)
        for k in range(len(x)):
            xx=(x[k]+t*speed[k])%W; yy=(y[k]+6*math.sin(t*.3+phase[k]))%H
            a=int(18+22*(.5+.5*math.sin(t*.9+phase[k]))); r=1.2 if k%4 else 2
            d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=(int(a*.32),int(a*.7),a))
        proc.stdin.write(img.tobytes())
    finish(proc); print('created particle layer',flush=True)

def implant():
    base=background(); proc=writer('implant.mp4')
    for frame in range(DURATION*FPS):
        t=frame/FPS; img=base.copy(); d=ImageDraw.Draw(img,'RGBA')
        d.text((43,30),'IMPLANTED ELECTRODES',font=BOLD,fill=(171,238,255,235))
        d.text((43,58),'SIMPLIFIED NON-GRAPHIC SCHEMATIC',font=SMALL,fill=(126,177,196,185))
        d.rounded_rectangle((44,100,916,440),radius=12,outline=(53,140,167,170),width=2,fill=(5,24,36,205))
        d.ellipse((85,181,532,580),fill=(35,83,97,240),outline=(107,194,211,200),width=3)
        for k in range(6):
            pts=[(x,273+k*32+12*math.sin(x*.025+k*1.35)+4*math.sin(x*.062+k)) for x in range(107,515,4)]
            d.line(pts,fill=(110,180,193,90),width=2)
        d.arc((78,144,540,550),182,358,fill=(155,186,193,200),width=18)
        d.arc((74,132,544,550),182,358,fill=(52,111,125,200),width=8)
        d.rounded_rectangle((265,178,363,197),radius=4,fill=(130,218,231,245),outline=(200,250,255,255),width=2)
        for x in range(275,358,16):
            d.line((x,194,x,246),fill=(168,231,239,235),width=3); d.ellipse((x-3,241,x+3,247),fill=(140,235,255,255))
        d.line([(363,187),(477,187),(503,157),(630,157)],fill=(81,183,211,210),width=4)
        q=(t*.23)%1; route=[(363,187),(477,187),(503,157),(630,157)]; ix=min(2,int(q*3)); r=q*3-ix
        px=route[ix][0]*(1-r)+route[ix+1][0]*r; py=route[ix][1]*(1-r)+route[ix+1][1]*r
        d.ellipse((px-5,py-5,px+5,py+5),fill=(197,252,255,255))
        d.rounded_rectangle((610,212,865,373),radius=8,outline=(81,180,204,220),width=2,fill=(7,38,52,230))
        d.text((630,231),'SIGNAL TO DECODER',font=FNT,fill=(170,224,237,230))
        pts=[(x,303+11*math.sin(x*.07-t*4)+4*math.sin((x*.07-t*4)*2.5)) for x in range(631,845,2)]
        d.line(pts,fill=(87,220,244,235),width=2)
        d.text((105,128),'SKULL',font=SMALL,fill=(155,207,219,205)); d.line((143,141,177,178),fill=(108,185,202,160),width=1)
        d.text((89,404),'BRAIN TISSUE',font=SMALL,fill=(155,207,219,205))
        d.text((244,106),'ELECTRODE ARRAY',font=SMALL,fill=(155,207,219,205)); d.line((315,125,315,175),fill=(108,185,202,160),width=1)
        proc.stdin.write(img.tobytes())
    finish(proc); print('created implant graphic',flush=True)

if __name__=='__main__':
    network(); bci(); particles(); implant()
