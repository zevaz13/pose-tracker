"""2D pose on still images: MediaPipe Pose Landmarker and RTMPose (rtmlib), COCO-17 output, joint angles."""
import os
from pathlib import Path

os.environ.setdefault("GLOG_minloglevel", "2")  # quieter MediaPipe logs

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision
from rtmlib import Body

ROOT = Path(__file__).resolve().parents[2]
MP_MODEL = ROOT / "models/mediapipe/pose_landmarker_full.task"
DET_MODEL = ROOT / "models/rtmlib/yolox_m_humanart.onnx"
POSE_MODEL = ROOT / "models/rtmlib/rtmpose_m_body7_256x192.onnx"

COCO = ["nose", "l_eye", "r_eye", "l_ear", "r_ear", "l_shoulder", "r_shoulder", "l_elbow", "r_elbow",
        "l_wrist", "r_wrist", "l_hip", "r_hip", "l_knee", "r_knee", "l_ankle", "r_ankle"]
MP33 = [p.name.lower() for p in vision.PoseLandmark]  # MediaPipe's 33 landmark names, in output order
MP_TO_COCO =[0, 2, 5, 7, 8, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
EDGES = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12),
         (11, 13), (13, 15), (12, 14), (14, 16), (0, 1), (0, 2), (1, 3), (2, 4)]


def load_image(path, long_side=None):
    """Read a photo as BGR (cv2 applies the EXIF orientation). Optionally downscale so the long side
    is `long_side` px. Returns (bgr, scale) where original_px = px / scale."""
    bgr = cv2.imread(str(path))
    if long_side is None or max(bgr.shape[:2]) <= long_side:
        return bgr, 1.0
    s = long_side / max(bgr.shape[:2])
    return cv2.resize(bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA), s


class MediaPipePose:
    """Pose Landmarker in IMAGE mode (each call independent, no tracking between images)."""

    def __init__(self, model=MP_MODEL, num_poses=1):
        opts = vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(model)),
                                            running_mode=vision.RunningMode.IMAGE, num_poses=num_poses)
        self.landmarker = vision.PoseLandmarker.create_from_options(opts)

    def __call__(self, bgr):
        """Returns (xy33 in px, visibility33), or NaNs if no person is found."""
        h, w = bgr.shape[:2]
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        res = self.landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
        if not res.pose_landmarks:
            return np.full((33, 2), np.nan), np.full(33, np.nan)
        lm = res.pose_landmarks[0]
        return np.array([[p.x * w, p.y * h] for p in lm]), np.array([p.visibility for p in lm])

    def close(self):
        self.landmarker.close()


def make_rtmpose(det=DET_MODEL, pose=POSE_MODEL):
    """Top-down RTMPose-m with the YOLOX-m person detector, weights loaded from models/."""
    return Body(det=str(det), det_input_size=(640, 640), pose=str(pose), pose_input_size=(192, 256),
                backend="onnxruntime", device="cpu")


def rtmpose_main_person(body, bgr):
    """Run rtmlib and keep the person with the highest mean keypoint score.
    Returns (xy17 px, score17, number of persons found)."""
    kpts, scores = body(bgr)
    if len(kpts) == 0:
        return np.full((17, 2), np.nan), np.full(17, np.nan), 0
    i = int(np.argmax(scores.mean(axis=1)))
    return kpts[i], scores[i], len(kpts)


def torso_px(xy):
    """Body scale: mean shoulder-to-hip length (both sides), px."""
    return float((np.linalg.norm(xy[5] - xy[11]) + np.linalg.norm(xy[6] - xy[12])) / 2)


def angle_deg(a, b, c):
    """Angle at b between b->a and b->c, degrees, in the image plane."""
    u, v = a - b, c - b
    return float(np.degrees(np.arccos(np.clip(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)), -1, 1))))


def joint_angles(xy):
    """Image-plane angles from COCO-17 keypoints (subject's left/right). Trunk lean = angle of the
    hip-midpoint -> shoulder-midpoint line from image vertical (0 = upright)."""
    out = {}
    for side, (s, e, w, h, k, a) in {"l": (5, 7, 9, 11, 13, 15), "r": (6, 8, 10, 12, 14, 16)}.items():
        out[f"{side}_elbow"] = angle_deg(xy[s], xy[e], xy[w])
        out[f"{side}_shoulder"] = angle_deg(xy[h], xy[s], xy[e])
        out[f"{side}_knee"] = angle_deg(xy[h], xy[k], xy[a])
    d = (xy[5] + xy[6]) / 2 - (xy[11] + xy[12]) / 2
    out["trunk_lean"] = float(np.degrees(np.arctan2(abs(d[0]), -d[1])))
    return out


def draw_skeleton(ax, xy, color, lw=2, label=None):
    for a, b in EDGES:
        ax.plot(*xy[[a, b]].T, color=color, lw=lw)
    ax.scatter(*xy.T, s=10, color="white", edgecolor=color, zorder=3, label=label)
