"""Stroke analysis on keypoint time series: speed, joint angles, stroke detection, per-stroke metrics.
Keypoints are COCO-17 arrays xy[F, 17, 2] in px with real-time stamps t[F] in s."""
import numpy as np
from scipy.signal import find_peaks, savgol_filter

SH, EL, WR, HIP = 6, 8, 10, 12  # COCO indices, right side (paddle arm)


def speed(xy, t, win, order=2):
    """Speed of a point track xy[F, 2] (px/s) from a Savitzky-Golay derivative over `win` frames.
    Assumes near-uniform frame spacing (check np.diff(t) first). Frames without a detection (NaN)
    stay NaN; the filter runs separately on each gap-free run of at least `win` frames."""
    dt = np.median(np.diff(t))
    v = np.full(len(xy), np.nan)
    edges = np.flatnonzero(np.diff(np.r_[0, np.isfinite(xy).all(axis=1).astype(int), 0]))
    for a, b in zip(edges[::2], edges[1::2]):
        if b - a >= win:
            v[a:b] = np.linalg.norm(savgol_filter(xy[a:b], win, order, deriv=1, delta=dt, axis=0), axis=-1)
    return v


def angle_series(xy, a, b, c):
    """Angle at joint b between b->a and b->c over time, degrees, image plane."""
    u, v = xy[:, a] - xy[:, b], xy[:, c] - xy[:, b]
    cos = (u * v).sum(1) / (np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1))
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def elbow_series(xy, torso, min_frac=0.3):
    """Right elbow angle, NaN where the upper arm or forearm is shorter than `min_frac` torso in the
    image (foreshortened, angle ill-conditioned). Returns (angle, short_mask)."""
    el = angle_series(xy, SH, EL, WR)
    short = ((np.linalg.norm(xy[:, SH] - xy[:, EL], axis=1) < min_frac * torso)
             | (np.linalg.norm(xy[:, EL] - xy[:, WR], axis=1) < min_frac * torso))
    el[short] = np.nan
    return el, short


def detect_strokes(v, t, min_gap_s=0.6, prominence=2, rel_height=0.6):
    """Stroke = peak of wrist speed v (torso/s): at least `min_gap_s` from a higher peak, `prominence`
    torso/s prominent, and at least `rel_height` x the 99th-percentile speed (drops backswing and
    return peaks). Returns (peak indices, half window in frames = half the median stroke period)."""
    dt = np.median(np.diff(t))
    pk, _ = find_peaks(np.nan_to_num(v), distance=int(min_gap_s / dt), prominence=prominence,
                       height=rel_height * np.nanpercentile(v, 99))
    half = int(np.median(np.diff(pk)) / 2) if len(pk) > 1 else int(0.5 / dt)
    return pk, half


def stroke_metrics(t, xy, v, elbow, peaks, half, torso):
    """One dict per stroke: t_peak, v_peak (torso/s), elbow at peak, elbow min/max in the window,
    wrist path length in the window (torso lengths)."""
    rows = []
    for n, p in enumerate(peaks, 1):
        lo, hi = max(0, p - half), min(len(t), p + half + 1)
        e = elbow[lo:hi]
        ok = np.isfinite(e).any()
        rows.append(dict(n=n, t_peak=t[p], v_peak=v[p], elbow_at_peak=elbow[p],
                         elbow_min=np.nanmin(e) if ok else np.nan, elbow_max=np.nanmax(e) if ok else np.nan,
                         path=np.linalg.norm(np.diff(xy[lo:hi, WR], axis=0), axis=1).sum() / torso))
    return rows
