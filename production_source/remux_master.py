#!/usr/bin/env python3
"""Create a continuous, loudness-normalized AAC track and embed chapter markers."""
import subprocess
from pathlib import Path
import imageio_ffmpeg
from script import SCENES

root=Path(__file__).resolve().parent; out=root.parent/'deliverables'
master=out/'AI_Uncovered_Digital_Immortality.mp4'; temp=out/'AI_Uncovered_master_remux.mp4'; metadata=root/'chapters.ffmeta'
offset=0; lines=[';FFMETADATA1\n','title=What If You Could Upload Your Brain Into a Computer?\n','artist=AI Uncovered\n']
for i,s in enumerate(SCENES):
    dur=s['duration']+(4 if i==7 else 0)+(15 if i==2 else 0)
    lines+=['[CHAPTER]\n','TIMEBASE=1/1000\n',f'START={offset*1000}\n',f'END={(offset+dur)*1000}\n',f'title={s["title"].title()}\n']; offset+=dur
metadata.write_text(''.join(lines),encoding='utf8')
audio=[(1,40),(2,50),(3,60),(9,15),(4,60),(5,60),(6,60),(7,50),(8,44)]
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','warning','-y','-filter_complex_threads','1','-i',str(master)]
for n,_ in audio: cmd+=['-i',str(root/'prepared'/f'voice_{n:02}.wav'),'-i',str(root/'prepared'/f'music_{n:02}.wav')]
meta_index=1+2*len(audio); cmd+=['-f','ffmetadata','-i',str(metadata)]
filters=[]; streams=[]
for i,(_,dur) in enumerate(audio):
    v=1+2*i; m=v+1
    filters.append(f'[{v}:a]apad,atrim=duration={dur},asetpts=PTS-STARTPTS,volume=1.12[v{i}]')
    filters.append(f'[{m}:a]atrim=duration={dur},asetpts=PTS-STARTPTS[m{i}]')
    filters.append(f'[v{i}][m{i}]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,aresample=48000,asetpts=PTS-STARTPTS[a{i}]')
    streams.append(f'[a{i}]')
filters.append(''.join(streams)+f'concat=n={len(audio)}:v=0:a=1,aresample=async=1:first_pts=0,'
    'loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=-18.08:measured_TP=-2.55:'
    'measured_LRA=4.30:measured_thresh=-29.15:offset=0:linear=false,aresample=48000[aout]')
cmd+=['-filter_complex',';'.join(filters),'-map','0:v:0','-map','[aout]','-map_metadata',str(meta_index),'-map_chapters',str(meta_index),
    '-c:v','copy','-c:a','aac','-b:a','128k','-ar','48000','-ac','2','-t',str(offset),'-movflags','+faststart',str(temp)]
subprocess.run(cmd,check=True); temp.replace(master)
print('Rebuilt continuous normalized audio and embedded chapters:',master,flush=True)
