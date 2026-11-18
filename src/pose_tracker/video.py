"""Per-frame 2D pose on video clips. Output follows the pipeline contract:
keypoints CSV with columns frame, t_s, joint, x_px, y_px, conf (raw model output)."""
import csv
import subprocess
import time

import cv2
import numpy as np
import mediapipe as mp

from .stills import COCO, MP33, MediaPipePose, make_rtmpose, rtmpose_main_person


def frame_times(path):
    """Presentation time of every video frame in s, from the container (not index / nominal fps)."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "frame=pts_time", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return np.array([float(l.strip(",")) for l in out.split() if l.strip(",")])


def iter_frames(path):
    """BGR frames; OpenCV applies the rotation flag, so phone portrait clips come out upright."""
    cap = cv2.VideoCapture(str(path))
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        yield frame
    cap.release()


def pose_video(path, model, out_csv):
    """Run `model` ('mediapipe' or 'rtmpose') on every frame and write the keypoints CSV.
    MediaPipe runs in VIDEO mode (tracks its ROI between frames, needs increasing timestamps);
    RTMPose runs YOLOX + RTMPose-m on every frame. Returns per-frame inference times in ms."""
    t = frame_times(path)
    if model == "mediapipe":
        mpp = MediaPipePose(running_mode=mp.tasks.vision.RunningMode.VIDEO)
        names = MP33
        run = lambda im, i: mpp(im, timestamp_ms=int(round(1000 * t[i])))
    else:
        body = make_rtmpose()
        names = COCO
        run = lambda im, i: rtmpose_main_person(body, im)[:2]
    ms = []
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["frame", "t_s", "joint", "x_px", "y_px", "conf"])
        for i, im in enumerate(iter_frames(path)):
            t0 = time.perf_counter()
            xy, conf = run(im, i)
            ms.append(1000 * (time.perf_counter() - t0))
            w.writerows((i, f"{t[i]:.6f}", names[j], f"{xy[j, 0]:.1f}", f"{xy[j, 1]:.1f}", f"{conf[j]:.3f}")
                        for j in range(len(names)))
    assert i + 1 == len(t), f"decoded {i + 1} frames, container has {len(t)}"
    if model == "mediapipe":
        mpp.close()
    return np.array(ms)


def read_keypoints(path):
    """Keypoints CSV -> (t_s[F], xy[F, J, 2], conf[F, J], joint names)."""
    a = np.genfromtxt(path, delimiter=",", names=True, dtype=None, encoding="utf-8")
    joints = list(dict.fromkeys(a["joint"]))
    F, J = len(np.unique(a["frame"])), len(joints)
    xy = np.stack([a["x_px"], a["y_px"]], axis=1).reshape(F, J, 2)
    return a["t_s"].reshape(F, J)[:, 0], xy, a["conf"].reshape(F, J), joints
