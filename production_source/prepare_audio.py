#!/usr/bin/env python3
"""Prepare aligned captions, narration, and an original ambient soundtrack."""
from __future__ import annotations
import math
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from pocketsphinx import Decoder
from scipy.io import wavfile
from script import SCENES

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'deliverables'; OUT.mkdir(exist_ok=True)
AUDIO=ROOT/'prepared'; AUDIO.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe(); SR=24000
PACINGS=[1.,1.,.97,.97,.97,.93,1.,1.]
BRIDGE=('Some brain-computer interfaces use artificial intelligence to decode patterns in brain signals. '
        'Artificial neural networks are simplified computational models, not complete copies of a biological brain.')

def display_tokens(text):
    return re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*(?:\.{2,}|[.,?!:;])?",text)

def spoken_words(token):
    token=re.sub(r"[.,?!:;]+$",'',token).lower()
    if token=='86': return ['eighty','six']
    if token=='bci': return ['b','c','i']
    if token=='ai': return ['a','i']
    return re.findall(r"[a-z]+(?:'[a-z]+)?",token.replace('-',' '))

def decode_narration(filename,pace=1):
    data=subprocess.check_output([FF,'-v','error','-i',str(ROOT/'audio'/filename),'-af',f'atempo={pace}',
        '-ar',str(SR),'-ac','1','-f','s16le','-'])
    return np.frombuffer(data,dtype='<i2').copy()

def align(samples,text):
    raw16=subprocess.check_output([FF,'-v','error','-f','s16le','-ar',str(SR),'-ac','1',
        '-i','-','-ar','16000','-ac','1','-f','s16le','-'],input=samples.tobytes())
    dec=Decoder(samprate=16000,loglevel='ERROR')
    if dec.lookup_word('cursors') is None: dec.add_word('cursors','K ER S ER Z',True)
    shown=display_tokens(text); words=[w for token in shown for w in spoken_words(token)]
    missing=sorted({w for w in words if dec.lookup_word(w) is None})
    if missing: raise ValueError(f'Missing pronunciations: {missing}')
    dec.set_align_text(' '.join(words)); dec.start_utt(); dec.process_raw(raw16,False,True); dec.end_utt()
    segments=list(dec.seg()); phonetic=[s for s in segments if not s.word.startswith('<')]
    if len(phonetic)!=len(words): raise RuntimeError(f'Alignment mismatch: {len(phonetic)} versus {len(words)}')
    items=[]; i=0
    for token in shown:
        n=len(spoken_words(token))
        if n:
            items.append({'text':token,'start':phonetic[i].start_frame/100,
                          'end':(phonetic[i+n-1].end_frame+1)/100})
            i+=n
    gaps=[(s.start_frame/100,(s.end_frame+1)/100) for s in segments
          if s.word=='<sil>' and s.end_frame-s.start_frame>=28]
    return items,gaps

def duration_str(sec,ass=False):
    sec=max(0,sec)
    if ass:
        ticks=int(round(sec*100)); h,ticks=divmod(ticks,360000); m,ticks=divmod(ticks,6000); s,cs=divmod(ticks,100)
        return f'{h}:{m:02}:{s:02}.{cs:02}'
    ms=int(round(sec*1000)); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def chunk_captions(items):
    cues=[]; chunk=[]
    for it in items:
        if chunk:
            candidate=' '.join(x['text'] for x in chunk+[it]); prior=chunk[-1]['text']
            too_long=len(candidate)>80 or it['end']-chunk[0]['start']>6.5
            sentence=bool(re.search(r'[?!]$|\.{1,}$',prior))
            comma=bool(re.search(r'[,;:]$',prior)) and len(' '.join(x['text'] for x in chunk))>=49
            long_pause=it['start']-chunk[-1]['end']>.65
            if sentence or ((too_long or comma or long_pause) and len(chunk)>=3):
                cues.append(chunk); chunk=[]
        chunk.append(it)
    if chunk: cues.append(chunk)
    for j in range(1,len(cues)):
        prior,cur=cues[j-1],cues[j]
        if len(cur)<=2 and len(' '.join(x['text'] for x in cur))<19 and len(prior)>5 and not re.search(r'[?!]$|\.{1,}$',prior[-1]['text']):
            boundaries=[k+1 for k,x in enumerate(prior[:-1]) if re.search(r'[,;:]$',x['text']) and len(prior)-(k+1)<=6]
            cut=boundaries[-1] if boundaries else max(2,len(prior)-4)
            cues[j-1],cues[j]=prior[:cut],prior[cut:]+cur
    out=[]
    for c in cues:
        text=' '.join(x['text'] for x in c)
        if len(text)>42:
            words=text.split(); target=len(text)/2
            _,at=min((abs(len(' '.join(words[:i]))-target),i) for i in range(1,len(words)))
            text=' '.join(words[:at])+'\n'+' '.join(words[at:])
        out.append((max(0,c[0]['start']-.05),c[-1]['end']+.08,text))
    for i in range(len(out)-1):
        st,en,text=out[i]; out[i]=(st,min(en,out[i+1][0]-.01),text)
    return out

ASS_HEADER='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,DejaVu Sans,52,&H00FFFFFF,&H000000FF,&H00101821,&H9A000000,-1,0,0,0,100,100,0,0,1,3.2,1.3,2,130,130,76,1
Style: Chapter,DejaVu Sans,34,&H00EADCB3,&H000000FF,&H00101821,&H80000000,-1,0,0,0,100,100,1,0,1,2,1,7,0,0,0,1
Style: Label,DejaVu Sans,25,&H00DBD6BF,&H000000FF,&H00101821,&H80000000,-1,0,0,0,100,100,0,0,1,1.5,1,9,0,0,0,1
Style: Fact,DejaVu Sans,51,&H00EDDCAC,&H000000FF,&H00101821,&H80000000,-1,0,0,0,100,100,0,0,1,2.5,1,7,0,0,0,1
Style: Wordmark,DejaVu Sans,98,&H00FFFFFF,&H000000FF,&H00101821,&H90000000,-1,0,0,0,100,100,4,0,1,3,1,5,0,0,0,1
Style: Tagline,DejaVu Sans,25,&H00EBD8A3,&H000000FF,&H00101821,&H90000000,-1,0,0,0,100,100,3,0,1,1.5,1,5,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
LABELS=['SPECULATIVE VISUALIZATION','ILLUSTRATIVE NEURAL MODEL','REAL BCI TECHNOLOGY  /  VISUAL RECONSTRUCTION',
    'HYPOTHETICAL  /  NOT YET ACHIEVED','HYPOTHETICAL  /  PERSONAL IDENTITY','SPECULATIVE FUTURE SCENARIOS',
    'NO PROVEN CONSCIOUSNESS TRANSFER','SPECULATIVE VISUALIZATION']
FACTS={2:[(9.6,14.8,'APPROX. 86 BILLION NEURONS')],3:[(45,57,'BRAIN SIGNALS  ≠  MIND UPLOADING')],
       4:[(25,33,'WHOLE-BRAIN EMULATION  /  HYPOTHETICAL')],5:[(48,58,'A COPY IS NOT PROOF OF CONTINUITY')],
       6:[(37,47,'PRIVACY  /  OWNERSHIP  /  SECURITY')],7:[(32,46,'NO PROVEN TRANSFER METHOD')],
       8:[(26,32,'WOULD YOU UPLOAD YOUR MIND?')]}

def ass_line(layer,start,end,style,text):
    return f'Dialogue: {layer},{duration_str(start,True)},{duration_str(end,True)},{style},,0,0,0,,{text}\n'

def write_ass(index,cues):
    content=ASS_HEADER
    for start,end,text in cues:
        content+=ass_line(0,start,end,'Sub',r'{\fad(90,90)}'+text.replace('\n',r'\N'))
    if index==9:
        content+=ass_line(2,.5,14.2,'Label',r'{\an9\pos(1816,85)\fad(500,600)}AI DECODING  /  NOT A MIND UPLOAD')
    else:
        scene=SCENES[index-1]
        content+=ass_line(2,.6,6.2,'Chapter',r'{\an7\move(85,98,105,98,0,700)\fad(450,650)}'+f'{index:02}  /  {scene["title"]}')
        content+=ass_line(2,6.7,scene['duration']-1,'Label',r'{\an9\pos(1816,85)\fad(500,700)}'+LABELS[index-1])
        for start,end,text in FACTS.get(index,[]):
            content+=ass_line(2,start,end,'Fact',r'{\an7\move(90,152,110,152,0,650)\fad(500,650)}'+text)
        if index==8:
            content+=ass_line(3,40.1,44,'Wordmark',r'{\an5\pos(960,510)\fad(700,500)}AI UNCOVERED')
            content+=ass_line(3,40.5,44,'Tagline',r'{\an5\pos(960,590)\fad(850,500)}EXPLORE WHAT COMES NEXT')
    (AUDIO/f'subtitles_{index:02}.ass').write_text(content,encoding='utf8')

def synth_music(scene_idx,duration,absolute_start,output_name=None):
    n=int(duration*SR); t=np.arange(n,dtype=np.float32)/SR; g=t+absolute_start
    roots=[73.416,65.406,58.270,73.416,65.406,87.307,58.270,73.416]; root=roots[scene_idx]
    chord=[1,1.259921 if scene_idx==5 else 1.189207,1.498307]
    envelope=.75+.25*np.sin(2*np.pi*.028*g+scene_idx)
    left=(.024*np.sin(2*np.pi*(root/2)*g)+.010*np.sin(2*np.pi*root*g+.4)).astype(np.float32)
    right=(.022*np.sin(2*np.pi*(root/2)*g+.12)+.011*np.sin(2*np.pi*root*g+.55)).astype(np.float32)
    for i,ratio in enumerate(chord):
        f=root*ratio; slow=.0065*(1+.3*np.sin(2*np.pi*(.045+i*.009)*g+i))
        left+=slow*np.sin(2*np.pi*f*g+i)*envelope
        right+=slow*np.sin(2*np.pi*f*1.0011*g+i+.5)*envelope
    left+=.004*np.sin(2*np.pi*root*4*g+2*np.sin(g*.07))*envelope
    right+=.004*np.sin(2*np.pi*root*4.01*g+2*np.sin(g*.071))*envelope
    period=2.3 if scene_idx not in (2,6) else 1.95; steps=[0,2,1,2,0,1,2,1]
    for beat in range(int(math.floor(absolute_start/period))-1,int(math.ceil((absolute_start+duration)/period))+1):
        when=beat*period-absolute_start; a=max(0,int(when*SR)); b=min(n,int((when+1.6)*SR))
        if b<=a: continue
        u=t[a:b]-when; f=root*4*chord[steps[beat%len(steps)]]
        decay=np.exp(-3*u)*(1-np.exp(-36*u)); pluck=.008*decay*(np.sin(2*np.pi*f*u)+.18*np.sin(2*np.pi*2*f*u))
        left[a:b]+=pluck; right[a:b]+=pluck*.86
    s=min(n,int(2.8*SR)); u=t[:s]
    impact=.033*np.exp(-2.6*u)*np.sin(2*np.pi*(42*u+7*(1-np.exp(-2*u))))
    whoosh=.006*np.sin(2*np.pi*(170*u+400*u*u))*np.exp(-1.5*u)
    left[:s]+=impact+whoosh; right[:s]+=impact-whoosh*.5
    if scene_idx==0 and duration>19:
        a=int(17.4*SR); b=min(n,a+int(1.5*SR)); u=np.arange(b-a,dtype=np.float32)/SR
        swell=.032*np.exp(-3*u)*np.sin(2*np.pi*(45*u+7*(1-np.exp(-2*u))))
        left[a:b]+=swell; right[a:b]+=swell
    if scene_idx==5:
        ramp=np.clip((t-35)/4,0,1); undertone=.009*ramp*np.sin(2*np.pi*34*g)
        left+=undertone; right+=undertone*.9
    if scene_idx==7:
        a=int(40*SR); b=min(n,a+int(3.5*SR)); u=np.arange(b-a,dtype=np.float32)/SR
        env=(1-np.exp(-22*u))*np.exp(-1.2*u)
        chime=.021*env*(np.sin(2*np.pi*440*u)+.5*np.sin(2*np.pi*660*u)+.25*np.sin(2*np.pi*880*u))
        left[a:b]+=chime; right[a:b]+=chime*.92
    if scene_idx==2:
        for when in [12,18,26,34,42]:
            a=int(when*SR); b=min(n,a+int(.22*SR))
            if b<=a: continue
            u=np.arange(b-a,dtype=np.float32)/SR; tick=.008*np.sin(2*np.pi*640*u)*np.exp(-20*u)
            left[a:b]+=tick; right[a:b]+=tick*.75
    fade=np.clip(np.minimum(1,np.minimum((t+.02)/.55,(duration-t)/.65)),0,1)
    stereo=np.column_stack((left*fade,right*fade))
    wavfile.write(AUDIO/(output_name or f'music_{scene_idx+1:02}.wav'),SR,np.int16(np.clip(stereo,-1,1)*32767))

def prepare_voice(index,text,duration,pace,offset,filename,start_pad=.45,expand_pauses=True):
    samples=decode_narration(filename,pace); source_duration=len(samples)/SR
    items,gaps=align(samples,text)
    desired=max(0,duration-source_duration-start_pad-1.1)
    usable=[(a,b) for a,b in gaps if a>.3 and b<source_duration-.25]
    per_gap=min(.78,desired/max(1,len(usable))) if expand_pauses else 0
    insertions=[((a+b)/2,per_gap) for a,b in usable if per_gap>.01]
    for item in items:
        item['start']+=start_pad+sum(d for p,d in insertions if p<item['start'])
        item['end']+=start_pad+sum(d for p,d in insertions if p<item['end'])
    chunks=[np.zeros(int(start_pad*SR),np.int16)]; previous=0
    for point,secs in insertions:
        center=int(point*SR); lo=max(previous,center-int(.08*SR)); hi=min(len(samples)-1,center+int(.08*SR))
        cut=lo+int(np.argmin(np.abs(samples[lo:hi].astype(np.int32))))
        chunks.extend((samples[previous:cut],np.zeros(int(secs*SR),np.int16))); previous=cut
    chunks.append(samples[previous:]); voice=np.concatenate(chunks); target=int(duration*SR)
    if len(voice)>target: raise RuntimeError(f'Scene {index} narration exceeds scene by {(len(voice)-target)/SR:.2f}s')
    wavfile.write(AUDIO/f'voice_{index:02}.wav',SR,np.pad(voice,(0,target-len(voice))))
    cues=chunk_captions(items); write_ass(index,cues)
    print('prepared',index,'source',round(source_duration,2),'cues',len(cues),flush=True)
    return [(a+offset,b+offset,text) for a,b,text in cues]

def main():
    combined=[]; offset=0
    for i,scene in enumerate(SCENES,1):
        combined+=prepare_voice(i,scene['text'],scene['duration'],PACINGS[i-1],offset,f'scene_{i:02}.mp3',.25 if i==8 else .45)
        synth_music(i-1,scene['duration']+(4 if i==8 else 0),offset)
        offset+=scene['duration']
        if i==3:
            combined+=prepare_voice(9,BRIDGE,15,1,offset,'ai_bridge.mp3',expand_pauses=False)
            synth_music(2,15,offset,'music_09.wav'); offset+=15
    subtitles=''.join(f'{i}\n{duration_str(a)} --> {duration_str(b)}\n{text}\n\n'
        for i,(a,b,text) in enumerate(combined,1))
    (OUT/'AI_Uncovered_Digital_Immortality.srt').write_text(subtitles.rstrip()+'\n',encoding='utf8')
    print('prepared',len(combined),'caption cues; total',offset+4,'seconds',flush=True)

if __name__=='__main__': main()
