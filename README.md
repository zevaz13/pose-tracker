# Pose Tracker (table-tennis strokes from phone video)

Status: PLANNING (2026-11-16). Nothing installed or measured yet. Part of the HobbyProjects backlog (section 8 in `hobby-ideas-backlog.md` in the Claude Project). Setup and run commands are in `docs/WORKFLOW.md`.

Legend: **[assumed]** = from literature or reasoning, not measured by me. **[verified]** = measured, with raw data in `test-logs/`. Everything below is [assumed] until a test log says otherwise.

## Goal
Measure body pose (limbs) of a table-tennis player from phone/tablet images, then from video of a stroke, then track the paddle through a backhand clip. See how far hobby-grade tools get, and learn where they break.

## Application (what the finished thing does)
A **stroke analyzer**, run offline on the computer. Input: a clip (or photo) from the phone/tablet. Output: (1) the video with skeleton and paddle trail drawn on it, (2) a metrics table per stroke (elbow angle at contact, peak wrist speed, paddle angle at contact, backswing-to-contact time), (3) a comparison across repeated strokes (consistency plot). The CV content is two parts:
- **Pose:** off-the-shelf 2D keypoint models, compared and evaluated against hand-labeled frames.
- **Tracking:** a paddle (later maybe the ball, see backlog section 3) through the clip: detection, then a motion model (Kalman filter), then smoothing. This is the part to build and tune myself.

## Decisions
- 2026-11-16: **All processing is offline on the computer.** The phone/tablet only record; no real-time or on-device requirement. Consequences: use full resolution and full fps; heavier models (ViTPose, SAM 2) are allowed; filters can use future frames (forward-backward / RTS smoothing), which fills gaps and reduces jitter compared with real-time filters. [assumed to help, to be measured]
- 2026-11-16: **2D first.** Keypoints and joint angles in the image plane, from a fixed camera. 3D is deferred.
  - Reason: single-view 3D has ambiguous depth, and the published monocular 3D result (OpenCap Monocular, 4.8 deg MAE rotations, 3.4 cm translations) was validated on walking, squatting and sit-to-stand, not on fast strokes. [assumed]
  - Note: two synchronized, calibrated views are the technical minimum for triangulating 3D (original OpenCap uses two or more smartphones). Phone + tablet already gives two views, more cameras would mainly help with occlusion. So 3D is a later stage, not blocked by hardware. [assumed]
- 2026-11-16: **Hardware for now = phone + tablet + tripod + shutter remote.** Cameras may be upgraded later.
  - **Phone: realme RMX3561 = realme GT Neo 3 5G** (a manual listing pairs the model number with that name). Spec sheets (realme, GSMArena): 4K at 30/60 fps, 1080p at 30 fps (60 fps listed with EIS), **slow-motion 720p at 480 fps**; front camera 1080p at 30 fps only. So the frame-rate tiers to test are 30 / 60 / 480 fps (no 120 or 240 listed). [assumed from spec sheets; the files are not checked yet: is 480 fps real capture, how long a clip, what resolution, how much light does it need?]
  - **Tablet:** the same Samsung Android tablet as the page-turner project (exact model not recorded here). Camera specs unknown. Role: second view for the optional 3D stage, or just a viewer. [assumed]
  - **Tripod:** available [reported by user]. Fixed camera, as the protocol requires.
  - **Wireless shutter:** the same Bluetooth remote as the page-turner ("Bluetooth remote RL7", sends Volume Up), to start/stop recording when the user is the subject. **[reported by user, 2026-11-16]:** the phone recognizes the button as Volume Up and the remote is paired with the phone. Bluetooth stays off on the tablet while the phone is in use (the tablet is not needed much for this project), so there is no pairing conflict. **[assumed, not yet tested]:** that the realme camera app starts/stops video recording with Volume Up (check its volume-button setting), and the idle wake-up behavior from the page-turner tests (first press after idle may be lost; untested).
- 2026-11-16: **Tool candidates for 2D pose:** MediaPipe Pose (33 landmarks, fast, CPU) and RTMPose via `rtmlib` (accurate on CPU). Compare both on the same clips; YOLO-pose or ViTPose only if those disappoint. OpenPose is not a starting point (older, replaced by these for new projects). [assumed]
- 2026-11-16: **GPU: none usable for CUDA. [verified] `lspci` shows only an Intel Iris Xe (TigerLake-LP GT2) integrated GPU; no NVIDIA card** (raw output in `test-logs/gpu-check-2026-11-16.txt`). The `nvidia-smi` "not found, install nvidia-utils" message is only apt's generic suggestion, not a sign of an NVIDIA GPU; do not install it. Plan: **everything on CPU** (MediaPipe and RTMPose are fine offline). Intel iGPU via OpenVINO (rtmlib backend) is an optional speed-up, not a requirement. Paddle-model training (Stage 2) is the only step that may want a GPU: decide then (tape tracker needs none; options are a small model on CPU, or Colab). [assumed for speeds]
- 2026-11-16: **Language: Python** for the whole pipeline (pose libraries, OpenCV, NumPy/SciPy, Matplotlib, Jupyter for exploration). `ffmpeg`/`ffprobe` as command-line tools. No C++/MATLAB needed. **[verified 2026-11-16]** system Python is 3.12.3 and `venv` works, so **no fresh Python install**: use **uv** (project rule from `CLAUDE.md`, 2026-11-16: only uv, never pip) with Python pinned to 3.12; check that `uv run python --version` reports the system 3.12.3 and does not download another interpreter [to verify]. Storage cost is the packages plus uv's cache. Other repos may use Python 3.14: no need to touch them. A PyPI wheel check shows every core package (mediapipe, rtmlib, onnxruntime, opencv-python, numpy, scipy, matplotlib) ships wheels for both 3.12 and 3.14, so either would work; 3.12 is already here. The only missing system tool, `ffmpeg`, was installed by the user on 2026-11-16 **[verified]**: `ffprobe version 6.1.1-3ubuntu5`. Details in `test-logs/machine-check-2026-11-16.txt`.
- 2026-11-16: **Machine [verified]:** Intel Core i7-1165G7 (4 cores / 8 threads per spec), 15 GiB RAM (about 10 GiB available, no swap), 142 GB free disk. Enough for MediaPipe and RTMPose on CPU; SAM 2 on CPU is untested and may be slow.
- 2026-11-16: **Measure, do not trust demos.** Accuracy under fast strokes is unknown for every tool. Ground truth = hand-labeled frames from a high-fps clip; practical metric = repeatability across repeated strokes (feeder session).

## Stages (each has a stop point)
- **Stage 0, stills (one evening):** side and front photos of a held ready position and backhand contact position. Overlay keypoints, compute elbow / shoulder / trunk / knee angles. Check against a protractor on a static pose. Noise floor = keypoint jitter between repeated photos of the same pose.
- **Stage 1, video:** per-frame keypoints, temporal filter (One Euro or Savitzky-Golay), wrist-speed curve, elbow angle over time, stroke phases. Same stroke at 30 vs. 60 vs. 480 fps (the phone's tiers) to quantify motion-blur and sampling loss.
- **Stage 2, paddle (backhand clip):** (1) colored tape on the blade + HSV segmentation, (2) wrist keypoint + fixed offset, (3) fine-tune YOLO-pose on a few hundred hand-labeled frames (SAM 2 can bootstrap labels from one click). Check RacketVision (arXiv 2511.17045) for data or weights.
- **Stage 3, optional 3D:** phone + tablet, checkerboard calibration, DLT triangulation of the 2D keypoints; or OpenCap Monocular on one clip. Sync with a clap or flash.
- **Link to the feeder:** repeatable balls give N identical backhands: spread of wrist path, contact angle and timing = consistency metric.

## Risks
- Motion blur and low fps degrade keypoints (indoor light needs short exposure). [assumed]
- Wrist/paddle occluded by the body in side views. [assumed]
- The paddle is small, fast and thin in profile; tags (ArUco) probably fail from blur. [assumed]
- Pixel-to-meter scale only valid for points in one plane (e.g. the table plane, 2.74 m x 1.525 m).
- Tablet camera quality and fps are unknown; it may only be useful as a second view at 30 fps.
- 480 fps is 720p and needs very short exposures (at most about 2 ms per frame): dark indoor lighting means noisy video. 60 fps at 1080p is the practical middle tier. [assumed]
- With the phone on a tripod facing the player, the screen is not visible: a missed remote press (idle wake-up, untested) could mean a missed recording. Mitigation: listen for the start tone, or leave margin and check the clip right after.
- Gyro-EIS / stabilization may crop or warp frames even on a tripod: turn it off for test clips if the app allows. [assumed]

## Open questions
- Phone (GT Neo 3): does the camera app really record 60 fps at 1080p and 480 fps at 720p? In the files (ffprobe, `docs/WORKFLOW.md` section 4): real frame rate, clip length limit, crop, and does 480 fps look usable under the lighting available (exposure is at most 1/480 s)?
- Does the realme camera app start/stop video recording with the Volume Up key (check its volume-button setting), and is there an audible start/stop tone? (Pairing with the phone is done; tablet Bluetooth is off while the phone is in use.)
- Tablet camera: model, max fps and resolution?
- Measured CPU speed: frames/s for MediaPipe and RTMPose on this i7-1165G7 (first Stage 0/1 benchmark), and whether SAM 2 (tiny) is usable on CPU.
- Camera upgrade later: what would matter most (higher fps, global-shutter-like behavior, lens)?

## Libraries (links)
**Pose, used from Stage 0**
- MediaPipe Pose Landmarker: docs https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python ; PyPI https://pypi.org/project/mediapipe/
- rtmlib (RTMPose without mmcv/mmpose): https://github.com/Tau-J/rtmlib ; PyPI https://pypi.org/project/rtmlib/
- RTMPose / MMPose (model zoo, background): https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose ; paper https://arxiv.org/abs/2303.07399
**Runtime and numerics, from Stage 0**
- ONNX Runtime: https://onnxruntime.ai/ ; PyPI https://pypi.org/project/onnxruntime/
- OpenCV (Python): https://pypi.org/project/opencv-python/ ; docs https://docs.opencv.org/
- NumPy https://pypi.org/project/numpy/ ; SciPy https://pypi.org/project/scipy/ ; Matplotlib https://pypi.org/project/matplotlib/
**Stage 2 and later (not installed now)**
- Ultralytics (YOLO pose, training, tracking): docs https://docs.ultralytics.com/tasks/pose ; PyPI https://pypi.org/project/ultralytics/
- SAM 2 (video segmentation for label bootstrapping): https://github.com/facebookresearch/sam2
- PyTorch (CPU build): https://pytorch.org/
- OpenVINO (optional Intel speed-up; rtmlib backend): https://pypi.org/project/openvino/

## Reading list (time-boxed: about 3 hours total; items 1-2 are enough to start Stage 0)
Skim for the API shape and the gotchas, then build. Do not read ahead of the stage you are on.
1. **MediaPipe Pose Landmarker, Python guide** (https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python), ~20 min. Take away: running modes IMAGE / VIDEO / LIVE_STREAM (use VIDEO for files; it needs increasing timestamps in ms), outputs both image-normalized landmarks and 3D "world" coordinates (the 3D is model-estimated, not measured).
2. **rtmlib README** (https://github.com/Tau-J/rtmlib), ~20 min. Take away: `Body` / `Wholebody` / `Custom` classes, `mode` = performance / lightweight / balanced, `device` = cpu / cuda / mps, `backend` = opencv / onnxruntime / openvino, models auto-download and cache. Then skim the RTMPose paper intro and results (arXiv 2303.07399).
3. **Concepts, not packages** (~30 min, any good survey): top-down vs. bottom-up pose, COCO 17-keypoint order, heatmap vs. SimCC vs. regression outputs, metrics OKS and PCK. Gotcha: confidence scores mean different things per model (heatmap peak, SimCC softmax, YOLO keypoint confidence, MediaPipe visibility), so do not compare them across models.
4. **Ultralytics pose docs** (https://docs.ultralytics.com/tasks/pose), ~30 min, read when starting Stage 2. Take away: the keypoint dataset format, `convert_coco` with keypoints, custom keypoint layouts, train/val/predict/export.
5. **SAM 2 README** (https://github.com/facebookresearch/sam2), ~30 min, Stage 2 only. Take away: video predictor with click prompts and `propagate_in_video`; needs python >= 3.10 and torch >= 2.5.1; smaller checkpoints exist for modest GPUs.
6. **ONNX Runtime CUDA execution provider** (https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider), only when going GPU. Take away: CUDA/cuDNN version pairing; always print `onnxruntime.get_available_providers()` to confirm the GPU is really used.
7. **OpenCV docs (no links verified yet; search by name):** `cv2.KalmanFilter`, and the camera calibration tutorial (needed only for Stage 3). **One Euro filter** (Casiez et al.) for keypoint smoothing; `scipy.signal.savgol_filter`; RTS smoother for offline forward-backward smoothing.
8. **Papers, skim only:** Kulkarni & Shenoy (2D pose for strokes), RacketVision (racket keypoints), OpenCap Monocular (Stage 3 only). Links under Sources.

## Sources
- rtmlib: https://github.com/Tau-J/rtmlib ; RTMPose paper: https://arxiv.org/abs/2303.07399
- MediaPipe Pose Landmarker (Python): https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python
- Ultralytics pose: https://docs.ultralytics.com/tasks/pose
- SAM 2: https://github.com/facebookresearch/sam2
- ONNX Runtime CUDA EP: https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider
- OpenCap Monocular (arXiv 2603.24733): https://arxiv.org/abs/2603.24733 ; code github.com/utahmobl/opencap-monocular ; https://opencap.ai
- Kulkarni & Shenoy, table-tennis stroke recognition with 2D pose: https://arxiv.org/abs/2104.09907
- RacketVision benchmark: https://arxiv.org/abs/2511.17045
- MediaPipe vs RTMPose vs OpenPose vs ViTPose overview: https://www.forasoft.com/learn/ai-for-video-engineering/articles-ai/openpose-mediapipe-rtmpose-pose-tracking
- Oxford comparison (MediaPipe, OpenPose, RTMPose, ViTPose, ...; infant video): https://ora.ox.ac.uk/objects/uuid:ff7ad4b5-3e9f-4d71-819d-15d19154a947/files/rhx11xh38d

## Log
- 2026-11-16: Remote `origin` added: private GitHub repo `zevaz13/pose-tracker` (SSH). Created on the web; Sebastian pushes.
- 2026-11-16: Git repository created (branch `main`, no remote; Sebastian reviews and pushes). `.gitignore` excludes `data/`, `models/`, `.venv/`. Removed the outdated root `WORKFLOW.md` (venv/pip version); `docs/WORKFLOW.md` is the only workflow file. uv 0.12.3 is installed [verified].
- 2026-11-16 (evening): User reports the remote is paired with the phone and recognized as Volume Up; tablet Bluetooth stays off while the phone is used (tablet not needed much for now). Still untested: whether the camera app records on Volume Up.
- 2026-11-16: Phone identified as realme GT Neo 3 (RMX3561): 4K/1080p at 30/60 fps, slow-mo 720p at 480 fps per spec sheets (to be verified on real files). User has a tripod and the Bluetooth shutter remote (for self-recording); tablet is the page-turner Samsung tablet. Frame-rate tiers to test: 30 / 60 / 480.
- 2026-11-16: ffmpeg installed (user ran `sudo apt install ffmpeg`); `ffprobe version 6.1.1-3ubuntu5` confirmed. No system tools missing. Next: user reads the reading list, then venv setup and Stage 0.
- 2026-11-16: Machine check: Python 3.12.3 + venv OK, ffmpeg missing, i7-1165G7, 15 GiB RAM, 142 GB free. PyPI wheel/size check: core packages are about 220 MB compressed (mediapipe 43 MB, opencv 74 MB, onnxruntime 28 MB, scipy 35 MB, numpy 16 MB, matplotlib 10 MB), plus opencv-contrib-python required by mediapipe/rtmlib. Decision: venv from system Python 3.12; no new Python install. Torch deferred to Stage 2 (CPU build).
- 2026-11-16: GPU check done: Intel Iris Xe only, no NVIDIA. Plan is CPU-only Python pipeline. Laptop is being refurbished with Linux; packages (python3-venv, ffmpeg) may still need installing.
- 2026-11-16: Added GPU plan (CPU first, GPU for training/SAM 2), reading list, and pipeline workflow (`docs/WORKFLOW.md` sections 8-9). Phone is a regular Android; GPU model still unchecked.
- 2026-11-16: Clarified: processing is offline on the computer; goal is a real CV project (pose from photo/video plus tracking an object) with a concrete application, the stroke analyzer above.
- 2026-11-16: Folder created. Scoped as 2D-first with phone + tablet; 3D deferred; staged plan and tool shortlist from a literature check (no measurements yet).
