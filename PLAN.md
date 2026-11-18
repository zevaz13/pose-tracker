# Pose tracker: plan

Current milestones: **M1, stills** (free-form set done; protocol photos with tape markers pending) and **M3, video** (60 fps and 480 fps backhand analyzed; forehand slow motion to re-record). Last updated 2026-11-18.

Rules: tick items as they are done, with the date. Decisions and findings go in `README.md`, commands in `docs/WORKFLOW.md`. Ask before any install, `sudo` or deletion.

## M0: environment
- [x] GPU check: Intel Iris Xe only, CPU plan (2026-11-16, `test-logs/gpu-check-2026-11-16.txt`)
- [x] Machine check and ffmpeg/ffprobe installed (2026-11-16, `test-logs/machine-check-2026-11-16.txt`)
- [ ] Sebastian reads the reading list (`README.md`)
- [x] Git repository: `git init -b main`, `.gitignore` for data/models/.venv; Sebastian pushes (2026-11-16)
- [x] Check `uv` is installed: uv 0.12.3 (2026-11-16)
- [x] `uv init` + pin Python 3.12; `uv run python --version` = system 3.12.3, no download (2026-11-16)
- [x] `uv add` core packages + notebook; `.venv` = 949 MB (2026-11-16)
- [x] Import check for cv2, mediapipe, rtmlib, onnxruntime: OK, CPU provider (2026-11-16)
- [x] Model weights (balanced set, 148 MB) in `models/`; package examples in `notebooks/00_package_examples.ipynb` (2026-11-16)
- [x] Folders: `src/pose_tracker/`, `scripts/`, `notebooks/`, `models/`, `data/derived/` (2026-11-16)

## M1: Stage 0, stills
- [x] Shooting protocol written: `docs/stills-protocol.md` (2026-11-16)
- [x] Free-form set `data/TableTennis1/` (17 photos, no markers): both models on all photos, keypoints and angles to `test-logs/`, skeleton overlays; `notebooks/02_tabletennis1_all_stills.ipynb` (2026-11-18)
- [x] Walkthrough on one photo: how each toolbox is called, crop/resolution, angle conditioning, timing; `notebooks/01_single_still_walkthrough.ipynb` (2026-11-18)
- [ ] ~15 photos per the protocol: side and front, ready and backhand contact, 5 still + 5 repeated shots, tape markers (waiting for good light)
- [ ] Script: MediaPipe and rtmlib on the same photos, keypoints to CSV in `test-logs/` (shared code done in `src/pose_tracker/stills.py`; CLI in `scripts/` still to write)
- [ ] Joint angles (elbow, shoulder, trunk, knee); compare with angles from the tape-marker centers
- [ ] Noise floor: spread over 5 still shots vs 5 repeated poses
- [ ] Stop point: do the models agree within a few degrees? Write findings in `README.md`

## M2: recording and clip checks
- [ ] Test the remote as record start/stop in the realme camera app (volume-button setting, start tone)
- [ ] Record the same backhand at 30, 60 and 480 fps (tripod)
- [x] `ffprobe` the first 5 clips: `test-logs/ffprobe_TableTennis1_vids_2026-11-18.txt` (60 fps: 1080p, clean 16.67 ms timing; slow motion: 720p, 480 fps capture written as 30 fps, tighter framing) (2026-11-18)
- [x] 480 fps is real capture (120 Hz light flicker sampled at 4 independent levels per cycle); light usable but flickers and is noisier (2026-11-18, notebook 04)
- [ ] Slow-motion clip length limit (not tested)
- [ ] Record the tablet model and camera specs (optional)

## M3: Stage 1, video
- [x] Per-frame keypoints to CSV (`scripts/pose_video.py`), wrist-speed curve (SG derivative), stroke detection, per-stroke metrics, elbow angle over time, consistency plots: `notebooks/03_video_60fps.ipynb` (2026-11-18)
- [ ] Filter stage writing `keypoints_<model>_filt.csv` (One Euro or SG / RTS)
- [ ] Side-view clip of forehand and backhand (the front view cannot measure their elbow angle), 10+ strokes each
- [x] 480 fps clips: `notebooks/04_video_480fps.ipynb`; backhand analyzed, forehand excluded (body out of frame) (2026-11-18)
- [ ] Re-record the slow-motion forehand with the whole body in frame (720p frame is tighter), 10+ strokes
- [x] Compare 60 vs 480 fps: decimating 480 fps to 60 fps keeps 79-86 % of the peak wrist speed (2026-11-18)
- [ ] Compare 30 fps too (optional)
- [ ] Hand-label ~30 frames, per-keypoint pixel error and PCK per model; choose the model
- [x] Measured CPU speed per model: MediaPipe VIDEO 21-27 ms/frame, RTMPose + YOLOX every frame 374-446 ms/frame (`test-logs/pose-speed_2026-11-18.csv`) (2026-11-18)

## M4: Stage 2, paddle
- [ ] Colored tape + HSV segmentation: centroid and blade angle
- [ ] Kalman / RTS smoothing of the track
- [ ] Only if needed: wrist + offset, or a fine-tuned keypoint model

## M5: analyzer and later
- [ ] Stroke segmentation and metrics table, annotated video, consistency plot
- [ ] Later, optional: 3D with phone + tablet, ball feeder sessions, gait
