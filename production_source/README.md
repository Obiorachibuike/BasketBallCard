# Editable documentary source

This folder retains the generated artwork, selected-voice narration clips, narration script, and Python production scripts. The finished video, thumbnail, SRT, and research notes are in `../deliverables/`. Artwork is illustrative AI-generated imagery; the neural traces are simulated.

## Rebuild

Install Python 3 and the `imageio-ffmpeg`, `pillow`, `numpy`, `scipy`, and `pocketsphinx` packages. DejaVu Sans fonts are expected at `/usr/share/fonts/truetype/dejavu/`. From the repository root:

```sh
python production_source/prepare_audio.py
python production_source/make_graphics.py
python production_source/create_thumbnail.py
python production_source/render_film.py
python production_source/remux_master.py
```

Intermediate audio and rendered segments can occupy several hundred megabytes during a rebuild. These intermediate files are ignored; the scripts recreate them. The soundtrack and effects are synthesized by `prepare_audio.py`.
