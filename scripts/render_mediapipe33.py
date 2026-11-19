"""Draw MediaPipe's 33 landmarks (numbered) on a clip, from the keypoints CSV of `pose_video.py`.

uv run python scripts/render_mediapipe33.py data/TableTennis1/vids/reves60.mp4
Reads data/derived/<clip folder>/<clip>_keypoints_mediapipe.csv and writes <clip>_mediapipe33.mp4 next to it
(H.264, source frame rate). Blue = subject's left, orange = right, grey = face and centre links;
small dot = visibility <= 0.5.
"""
import argparse
import subprocess
from pathlib import Path

import cv2
import numpy as np
from mediapipe.tasks.python import vision

from pose_tracker.stills import ROOT, MP33
from pose_tracker.video import iter_frames, read_keypoints

EDGES = [(c.start, c.end) for c in vision.PoseLandmarksConnections.POSE_LANDMARKS]
SIDE = ["l" if n.startswith("left") else "r" if n.startswith("right") else "c" for n in MP33]
COL = {"l": (214, 120, 42), "r": (52, 104, 235), "c": (160, 160, 160)}  # BGR


def render(clip):
    der = ROOT / "data/derived" / clip.parent.relative_to(ROOT / "data")
    t, xy, conf, names = read_keypoints(der / f"{clip.stem}_keypoints_mediapipe.csv")
    assert names == MP33
    fps = (len(t) - 1) / (t[-1] - t[0])
    out = der / f"{clip.stem}_mediapipe33.mp4"
    ff = None
    for i, fr in enumerate(iter_frames(clip)):
        if ff is None:
            h, w = fr.shape[:2]
            ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                                   "-r", f"{fps:.4f}", "-i", "-", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                                   str(out)], stdin=subprocess.PIPE)
        if np.isfinite(xy[i]).all():
            p = np.round(xy[i]).astype(int)
            for a, b in EDGES:
                cv2.line(fr, tuple(p[a]), tuple(p[b]), COL[SIDE[a] if SIDE[a] == SIDE[b] else "c"], 3, cv2.LINE_AA)
            for j in range(33):
                r = 7 if conf[i, j] > 0.5 else 4
                cv2.circle(fr, tuple(p[j]), r, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(fr, tuple(p[j]), r, COL[SIDE[j]], 2, cv2.LINE_AA)
                cv2.putText(fr, str(j), tuple(p[j] + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(fr, f"MediaPipe 33 landmarks  t={t[i]:.2f}s", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3,
                    cv2.LINE_AA)
        ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    assert i + 1 == len(t), f"decoded {i + 1} frames, CSV has {len(t)}"
    return out


p = argparse.ArgumentParser()
p.add_argument("clips", nargs="+", type=Path)
for clip in p.parse_args().clips:
    out = render(clip.resolve())
    print(out.relative_to(ROOT), f"{out.stat().st_size / 1e6:.1f} MB")
