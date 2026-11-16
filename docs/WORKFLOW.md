# Pose Tracker: Workflows

Setup, recording, running. Findings and decisions live in `../README.md`. Nothing here has been run yet (2026-11-16); commands are the plan.

## 1. Where things live
- `~/HobbyProjects/pose-tracker/`
  - `CLAUDE.md`: context for Claude Code (rules, facts, conventions)
  - `PLAN.md`: current milestone checklist
  - `README.md`: findings, decisions, risks, open questions, dated log
  - `docs/WORKFLOW.md`: this file (setup, recording, running)
  - `.gitignore`: keeps `data/`, `models/`, `.venv/` out of git
  - `data/`: raw photos and clips (large, never modified, not for git). Name: `YYYY-MM-DD_<device>_<fps>fps_<what>_<take>.<ext>`, e.g. `2026-11-20_phone_480fps_backhand_03.mp4`
  - `data/derived/`: regenerable pipeline outputs (keypoints, filtered, paddle, strokes CSVs; not for git)
  - `test-logs/`: small results worth keeping (jitter and pixel-error tables, ffprobe outputs, hand labels), named with model/device and date
  - scripts (planned): `pose_stills.py`, `pose_video.py`, `compare_models.py`
- Folders `data/`, `docs/` and `test-logs/` exist. Create the rest: `mkdir -p ~/HobbyProjects/pose-tracker/data/derived`

## 2. Python setup with uv (not done; ask before installing)
**Rule: `uv` only, never `pip` or `pip3`** (project rule in `CLAUDE.md`). No fresh Python install should be needed: the system Python is 3.12.3 (verified 2026-11-16) and every core package ships wheels for both 3.12 and 3.14. Other repos on this machine may use Python 3.14: leave them alone (separate environments, nothing shared).
```
cd ~/HobbyProjects/pose-tracker
uv --version                              # is uv installed? If not, ask Sebastian before installing it
uv python list                            # interpreters uv can see: expect the system 3.12.3
uv init --bare --vcs none --python 3.12   # only pyproject.toml, no sample files; --vcs none because git is already set up (check the flags with `uv init --help`)
uv python pin 3.12                        # writes .python-version
uv run python --version                   # expect 3.12.3; if uv wants to download a Python, stop and ask Sebastian
uv add mediapipe rtmlib onnxruntime numpy scipy matplotlib   # opencv comes in as a dependency of rtmlib/mediapipe
uv add --dev notebook                     # for exploration
uv run python -c "import cv2, mediapipe, rtmlib, onnxruntime; print(cv2.__version__, onnxruntime.get_available_providers())"
uv run jupyter notebook
```
`uv` creates `.venv/` and `uv.lock` in the project and keeps a download cache (`uv cache dir`) that uses extra disk; `uv cache clean` frees it (ask first). Remove the environment with `rm -rf .venv` (ask first): `uv sync` recreates it from `uv.lock`. That the system Python is picked without a download is assumed until the `uv run python --version` check above.

**Expected download sizes (compressed wheels from PyPI, 2026-11-16; installed size is larger, estimate under 1 GB total, to be measured with `du -sh .venv`, plus uv's cache):** mediapipe 43 MB, opencv-python 74 MB (rtmlib and mediapipe also require `opencv-contrib-python`, a similar size), onnxruntime 28 MB, scipy 35 MB, numpy 16 MB, matplotlib 10 MB, rtmlib 0.1 MB, notebook and its dependencies (size not checked). Model weights are downloaded separately on first use (sizes not checked): note them. If `import cv2` ever fails because the two OpenCV packages overlap, find the root cause first (`uv tree` shows who requires which), do not guess.
**Not now (Stage 2 only):** `torch` (the PyPI Linux build is 539 MB and also pulls large NVIDIA CUDA libraries that are useless without an NVIDIA GPU; use PyTorch's CPU build instead and check its size first), `ultralytics` (pulls torch), SAM 2. `openvino` (59 MB) is an optional speed-up for the Intel iGPU/CPU.
- `rtmlib` runs RTMPose through ONNX Runtime (lighter than `mmpose`/PyTorch). It downloads model weights on first use: note the size.
- GPU: none (Intel Iris Xe only, checked 2026-11-16). Use plain `onnxruntime` (CPU). Do not install `onnxruntime-gpu` or NVIDIA packages.
- System packages: Python 3.12.3 and `venv` are already present (verified). `ffmpeg` was missing and was installed on 2026-11-16 (`sudo apt install ffmpeg`, run by the user); `ffprobe version 6.1.1-3ubuntu5` verified. Nothing else needs `sudo`.
- Machine facts (verified 2026-11-16, in `test-logs/machine-check-2026-11-16.txt`): i7-1165G7, 15 GiB RAM, 142 GB free.
- MediaPipe model files (`.task`) are downloaded separately; save them under `models/` (not for git).

## 3. Recording protocol (fixed camera)
Goal: clean, comparable clips. Change one thing at a time.
1. Camera on a tripod or propped at about table height, **fixed** (no hand-holding), landscape, side view roughly perpendicular to the stroke plane for the first tests. Whole body and paddle in frame, with margin.
2. Lock exposure, focus and white balance if the camera app allows; turn off auto-zoom / stabilization if possible.
3. Bright, even light (short shutter = less blur). Clothes that contrast with the background.
4. Frame-rate tiers on the realme GT Neo 3 (per spec sheets, to verify): **30 fps and 60 fps at 1080p (or 4K)** in normal video, and **slow-motion 720p at 480 fps**. Record the same stroke at each tier for comparison. 480 fps needs lots of light (exposure at most 1/480 s) and may crop or limit clip length: note which. Turn off stabilization (EIS) for test clips if the app allows.
5. First 2 s: stand still in a neutral pose (gives the static noise floor). Then 5-10 strokes. For a scale reference, keep the table (2.74 m x 1.525 m) visible or put a known-length marker in the stroke plane.
6. **Self-recording with the Bluetooth remote (to test):** the remote is paired with the phone and recognized as Volume Up (user-reported 2026-11-16); keep Bluetooth off on the tablet while the phone is in use (re-pair when switching back to the page-turner, since the remote probably holds one connection at a time). In the camera app, check the volume-button setting (shutter/record vs. zoom). Press once, listen for the start tone (the phone faces you, so the screen is not visible), and if there is none, press again. Always check the first clip right after recording. The 2 s standing pose at the start doubles as a buffer for a late start. Keep a hand tap on the screen as the fallback start/stop.
7. For the later 3D stage: record a checkerboard (many poses) with each camera before or after, and clap or flash at the start for sync.

## 4. Getting clips onto the computer
Phone and tablet are both Android, so adb works for either. With two devices connected, name the one you want:
```
adb devices
adb -s <device-id> shell ls /sdcard/DCIM/Camera | tail
adb -s <device-id> pull /sdcard/DCIM/Camera/<file>.mp4 ~/HobbyProjects/pose-tracker/data/
```
Check the real frame rate and timing of every clip before trusting the app's label (some phones write slow-mo files with a stretched timeline or variable frame rate):
```
ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate,r_frame_rate,width,height,nb_frames,duration -of default=nw=1 clip.mp4
```
Log the result in `data/clips.csv` (file, device, fps, resolution, what, notes).
Do not write device IDs (serials) into the README or commits. USB debugging must be enabled on the phone too (same steps as the tablet in `page-turner/WORKFLOW.md`, section 2). A cable-free alternative is any file-sharing method you prefer.

## 5. Stage 0 checklist (stills)
1. 6-10 photos: side and front, ready position and backhand contact position, same camera position.
2. Run each model on all photos, save the 17 (COCO) or 33 (MediaPipe) keypoints to CSV in `test-logs/`.
3. Compute elbow, shoulder, trunk-lean and knee angles from 2D keypoints.
4. Take a protractor/goniometer reading of one static elbow angle; compare.
5. Repeat the same pose 5 times without moving the camera: jitter between repeats = noise floor.

What to look for: do the angles agree between models within a few degrees? Is the wrist keypoint stable? Do limbs get swapped or dropped when an arm crosses the body?

## 6. Stage 1 checklist (video), after Stage 0
- Per-frame keypoints to CSV, then filter, then wrist speed (pixels/s, or m/s once a scale is set) and joint angles over time.
- Compare 30 vs. 60 vs. 480 fps of the same stroke: fraction of frames with low-confidence or jumping keypoints.
- Pixel-error test: hand-label ~30 frames of one 480 fps (or the best verified) clip, compute per-keypoint error and PCK per model; save labels and results to `test-logs/`.
- Repeatability: across N strokes of one session, spread of wrist path and contact angle.

## 7. Paddle (Stage 2), later
Start with colored tape on the blade (HSV segmentation, centroid and blade angle). Only move to a trained keypoint model if the tape approach is not enough. Details in `../README.md`.

## 8. GPU check (done 2026-11-16: Intel Iris Xe only, no NVIDIA; the rest of this section applies only if hardware changes)
Note on reading the output: `grep -iE 'vga|3d|display'` also matches storage devices whose name contains "3D" (e.g. an NVMe SSD), and the `nvidia-smi: command not found` message lists apt packages even on machines without NVIDIA hardware. Only the `VGA compatible controller` / `3D controller` lines are GPUs.
```
lspci | grep -iE 'vga|3d|display'      # which GPUs exist (laptops often have an integrated one plus a discrete one)
nvidia-smi                             # NVIDIA only: model, VRAM, driver, max CUDA version
```
Linux Mint: the Driver Manager shows whether the proprietary NVIDIA driver is active. If `nvidia-smi` fails but `lspci` lists an NVIDIA card, the driver is not loaded (changing it is a system change: ask first).
- **NVIDIA:** PyTorch (Ultralytics, SAM 2) installs with CUDA wheels in the venv. `onnxruntime-gpu` needs matching CUDA/cuDNN (current PyPI builds target CUDA 12.x and cuDNN 9). After install, run `python -c "import onnxruntime as o; print(o.get_available_providers())"`: it must list `CUDAExecutionProvider`, otherwise it silently runs on CPU.
- **AMD or Intel graphics:** use CPU for MediaPipe and rtmlib; rtmlib also has an OpenVINO backend (Intel). Training a paddle model on CPU is slow; Google Colab free GPU is the fallback for that single step (ask first: uploads your clips).
- **Where the GPU matters:** training/fine-tuning a keypoint model (Stage 2), SAM 2 label bootstrapping. **Where it does not:** MediaPipe, and RTMPose on offline clips (even at 10 frames/s on CPU, a 5 s clip at 240 fps = 1,200 frames takes about 2 minutes).
- Save the outputs in `test-logs/gpu-check-2026-11-16.txt` and update the README open question (`../README.md`).

## 9. Pipeline layout (one file per stage, so stages can be re-run and compared)
```
clip.mp4 --(extract)--> frames or direct decode
        --(pose)-----> keypoints_<model>.csv      frame, t_s, joint, x_px, y_px, conf
        --(filter)---> keypoints_<model>_filt.csv  same columns, smoothed (One Euro / RTS)
        --(track)----> paddle.csv                  frame, t_s, cx, cy, angle_deg, conf
        --(metrics)--> strokes.csv                 stroke id, t_contact, elbow_deg, wrist_speed_peak, paddle_angle, ...
        --(report)---> annotated.mp4 + plots/
```
Rules: timestamps from the video's own frame times (not frame index / nominal fps); keep raw model output untouched and filter in a separate file; one script per arrow, driven by command-line arguments; every experiment writes into `test-logs/` with model name and date. Explore in a notebook, then move the working code into scripts.

## 10. Order of work
1. Environment + GPU check (sections 2, 8). Report download sizes first.
2. Stage 0 on 6-10 stills with MediaPipe, then rtmlib, same photos.
3. Record the same backhand at 30, 60 and 480 fps (tripod, remote), log each with ffprobe: is 480 fps real, and is it usable in this lighting?
4. Stage 1 on that clip: keypoints, filter, wrist-speed curve, plot.
5. Hand-label ~30 frames, compute per-model pixel error. Decide the model.
6. Stage 2 (tape tracker first). Only then decide about training and 3D.

