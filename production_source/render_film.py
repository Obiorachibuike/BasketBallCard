#!/usr/bin/env python3
"""Render the 1080p documentary from the generated production assets."""
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path
import imageio_ffmpeg
from script import SCENES

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'rendered'; OUT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe(); FPS=24; FADE=.75
EDITS=[
 [('10_mind.jpg',9,'left',1.03),('01_brain_lab.jpg',16,'center',1.03),('09_processor.jpg',26,'right',1.04),('01_brain_lab.jpg',40,'center',1.09)],
 [('01_brain_lab.jpg',11,'center',1.04),('02_neurons.jpg',24,'left',1.04),('network.mp4',37,'video',1.),('04_scan.jpg',50,'center',1.04)],
 [('03_bci.jpg',16,'center',1.02),('bci.mp4',28,'video',1.),('03_bci.jpg',32,'left',1.16),('implant.mp4',37,'video',1.),('03_bci.jpg',60,'right',1.07)],
 [('04_scan.jpg',14,'center',1.04),('network.mp4',28,'video',1.),('08_incomplete.jpg',42,'right',1.02),('09_processor.jpg',60,'center',1.06)],
 [('05_identity.jpg',16,'center',1.03),('10_mind.jpg',27,'left',1.04),('05_identity.jpg',41,'left',1.16),('05_identity.jpg',60,'right',1.16)],
 [('06_city.jpg',15,'center',1.03),('05_identity.jpg',28,'right',1.12),('06_city.jpg',36,'center',1.13),('07_servers.jpg',60,'center',1.02)],
 [('08_incomplete.jpg',17,'center',1.03),('network.mp4',30,'video',1.),('02_neurons.jpg',40,'right',1.08),('08_incomplete.jpg',50,'right',1.11)],
 [('06_city.jpg',15,'center',1.04),('10_mind.jpg',26,'left',1.05),('09_processor.jpg',44,'center',1.02)],
 [('bci.mp4',7,'video',1.),('network.mp4',15,'video',1.)],
]

def esc(path): return str(path).replace('\\','\\\\').replace(':',r'\:').replace("'",r"\'")

def build_command(scene_no,sample=None):
    duration=15 if scene_no==9 else SCENES[scene_no-1]['duration']+(4 if scene_no==8 else 0)
    shots=EDITS[scene_no-1]; cmd=[FF,'-hide_banner','-loglevel','warning','-y','-filter_complex_threads','1']
    for name,_,kind,_ in shots:
        file=ROOT/('graphics' if kind=='video' else 'shots')/name
        if kind=='video': cmd+=['-stream_loop','-1']
        cmd+=['-i',str(file)]
    particle_idx=len(shots); cmd+=['-stream_loop','-1','-i',str(ROOT/'graphics'/'particles.mp4')]
    voice_idx=particle_idx+1; music_idx=particle_idx+2
    cmd+=['-i',str(ROOT/'prepared'/f'voice_{scene_no:02}.wav'),'-i',str(ROOT/'prepared'/f'music_{scene_no:02}.wav')]
    filters=[]; previous=0
    for i,(_,end,kind,start_zoom) in enumerate(shots):
        length=(end-previous)+(FADE if i<len(shots)-1 else 0); frames=round(length*FPS)
        if kind=='video':
            filters.append(f'[{i}:v]trim=duration={length:.3f},setpts=PTS-STARTPTS,scale=1920:1080:flags=bilinear,fps={FPS},setsar=1,format=yuv420p,settb=1/24[v{i}]')
        else:
            if kind=='left': xpos=f'0.12+0.18*on/{frames}'
            elif kind=='right': xpos=f'0.88-0.18*on/{frames}'
            else: xpos=f'0.46+0.08*on/{frames}'
            z=f'{start_zoom:.3f}+0.085*on/{frames}'
            filters.append(f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='{z}':x='(iw-iw/zoom)*({xpos})':y='(ih-ih/zoom)*0.48':d={frames}:s=1920x1080:fps={FPS},setsar=1,format=yuv420p,settb=1/24,setpts=PTS-STARTPTS[v{i}]")
        previous=end
    last='v0'
    for i in range(1,len(shots)):
        out=f'xf{i}'; filters.append(f'[{last}][v{i}]xfade=transition=fade:duration={FADE}:offset={shots[i-1][1]}[{out}]'); last=out
    # RGB is essential: applying screen blend to YUV chroma tints the image.
    filters.append(f'[{last}]format=gbrp[base_rgb]')
    filters.append(f'[{particle_idx}:v]scale=1920:1080:flags=bilinear,fps={FPS},format=gbrp,settb=1/24,setpts=PTS-STARTPTS[particles]')
    filters.append('[base_rgb][particles]blend=all_mode=screen:all_opacity=0.38:shortest=1,scale=out_range=tv:out_color_matrix=bt709,format=yuv420p,setparams=range=limited:colorspace=bt709:color_primaries=bt709:color_trc=bt709[motion]')
    ass=esc(ROOT/'prepared'/f'subtitles_{scene_no:02}.ass')
    filters.append(f"[motion]ass=filename='{ass}':fontsdir='/usr/share/fonts/truetype/dejavu',fade=t=in:st=0:d=0.35,fade=t=out:st={duration-.4}:d=0.4,format=yuv420p[vout]")
    filters.append(f'[{voice_idx}:a]apad,atrim=duration={duration},volume=1.12[voice]')
    filters.append(f'[{music_idx}:a]atrim=duration={duration}[music]')
    filters.append('[voice][music]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,aresample=48000[aout]')
    cmd+=['-filter_complex',';'.join(filters),'-map','[vout]','-map','[aout]','-t',str(sample or duration),'-r',str(FPS),
        '-c:v','libx264','-preset','veryfast','-crf','23','-maxrate','1500k','-bufsize','3000k',
        '-pix_fmt','yuv420p','-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',
        '-g','48','-threads','2','-c:a','aac','-b:a','128k','-ar','48000','-ac','2','-movflags','+faststart']
    output=ROOT/f'sample_{scene_no:02}.mp4' if sample else OUT/f'scene_{scene_no:02}.mp4'
    cmd.append(str(output)); return cmd,output

def render(scene_no,sample=None):
    cmd,out=build_command(scene_no,sample); print(f'RENDER chapter {scene_no}',flush=True)
    subprocess.run(cmd,check=True); print(f'COMPLETE chapter {scene_no}: {out.stat().st_size/1024/1024:.1f} MiB',flush=True)

def join():
    deliver=ROOT.parent/'deliverables'; deliver.mkdir(exist_ok=True); manifest=OUT/'concat.txt'; order=[1,2,3,9,4,5,6,7,8]
    manifest.write_text(''.join(f"file '{(OUT/f'scene_{i:02}.mp4').as_posix()}'\n" for i in order))
    output=deliver/'AI_Uncovered_Digital_Immortality.mp4'
    subprocess.run([FF,'-hide_banner','-loglevel','warning','-y','-f','concat','-safe','0','-i',str(manifest),
        '-map','0:v:0','-c:v','copy','-an','-movflags','+faststart',str(output)],check=True)
    print(f'Joined picture: {output.stat().st_size/1024/1024:.1f} MiB',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--scene',type=int,choices=range(1,10)); parser.add_argument('--sample',type=float)
    parser.add_argument('--join-only',action='store_true'); args=parser.parse_args()
    if args.join_only: join()
    elif args.scene: render(args.scene,args.sample)
    else:
        for i in range(1,10): render(i)
        join()
