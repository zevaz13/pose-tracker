"""Pipeline stage 'pose': per-frame keypoints for video clips.

uv run python scripts/pose_video.py data/TableTennis1/vids/chop60.mp4 --model rtmpose
Writes data/derived/<clip folder>/<clip>_keypoints_<model>.csv and appends a speed line to
test-logs/pose-speed_<date>.csv.
"""
import argparse
import datetime
from pathlib import Path

import numpy as np

from pose_tracker.stills import ROOT
from pose_tracker.video import pose_video

p = argparse.ArgumentParser()
p.add_argument("clips", nargs="+", type=Path)
p.add_argument("--model", choices=["mediapipe", "rtmpose"], required=True)
args = p.parse_args()

date = datetime.date.today().isoformat()
speed_log = ROOT / f"test-logs/pose-speed_{date}.csv"
new = not speed_log.exists()
for clip in args.clips:
    clip = clip.resolve()
    out_dir = ROOT / "data/derived" / clip.parent.relative_to(ROOT / "data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{clip.stem}_keypoints_{args.model}.csv"
    ms = pose_video(clip, args.model, out)
    line = (f"{clip.name},{args.model},{len(ms)},{ms.sum()/1000:.1f},{np.median(ms):.1f},{ms.min():.1f},"
            f"{np.median(ms[1:]):.1f}")
    print(line, "->", out.relative_to(ROOT))
    with open(speed_log, "a") as f:
        if new:
            f.write("clip,model,frames,total_s,median_ms,min_ms,median_ms_excl_first\n"); new = False
        f.write(line + "\n")
