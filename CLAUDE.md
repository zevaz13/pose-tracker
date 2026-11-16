# Pose tracker (Claude Code context)

Root conventions are in `../CLAUDE.md` (who Sebastian is, ask-before rules, short replies, verified vs assumed). This file adds what is specific to this project and wins where they differ.

Read first, in this order: `PLAN.md` (current milestone and checklist), `README.md` (decisions, risks, open questions, dated log), `docs/WORKFLOW.md` (setup and commands). Do not start work before reading `PLAN.md`.

## Role
Act as an experienced computer vision and data analysis researcher: pose estimation, tracking, filtering, evaluation. Sebastian is an expert, so skip basics and show commands and what to look for.

## Goal
Offline stroke analyzer for table tennis. Input: photos and clips from the phone. Output: skeleton and paddle trail drawn on the video, a metrics table per stroke, a consistency plot across repeated strokes. Order: 2D pose on stills, then video, then paddle tracking through a backhand clip. 3D is deferred. Gait analysis is a possible later use of the same pipeline.

## Established facts (details and sources in `README.md`)
- All processing is offline on the laptop. The phone and tablet only record.
- Machine (verified 2026-11-16): Linux, Python 3.12.3, ffmpeg/ffprobe 6.1.1 installed, i7-1165G7, 15 GiB RAM, 142 GB free. GPU is Intel Iris Xe only: no CUDA. Everything runs on CPU. Never install NVIDIA, CUDA or `onnxruntime-gpu` packages.
- Models: MediaPipe Pose Landmarker and RTMPose via `rtmlib` (ONNX Runtime). Compare both on the same files. YOLO-pose and ViTPose only if those disappoint.
- Camera: realme GT Neo 3 (RMX3561) on a tripod. Frame-rate tiers to test: 30, 60, 480 fps (480 fps is 720p). Spec sheet values, not yet verified in files. Check every clip with `ffprobe` before trusting the label (command in `docs/WORKFLOW.md`, section 4).
- Shutter remote: the same Bluetooth remote as page-turner, sends Volume Up. Whether the realme camera app records on it is untested.
- Environment installed 2026-11-16 (uv, Python 3.12.3, `.venv` 949 MB). Torch, ultralytics and SAM 2 are deferred to Stage 2 (CPU torch build only; check the size first).
- Code layout: shared code in `src/pose_tracker/` (import as `pose_tracker`), one CLI per stage in `scripts/`, exploration and parameter tuning in `notebooks/`. Notebooks import from `pose_tracker`; settled code moves out of notebooks into `src/`.

## Python and tooling
- Use `uv` exclusively for all Python tasks. Never `pip` or `pip3`.
  ```bash
  uv add <package>          # add a dependency
  uv run python <script>    # run without activating the venv
  uv run jupyter notebook   # notebooks
  ```
- Python is pinned to 3.12 (system interpreter). If `uv` wants to download another Python, stop and ask. Other repos on this machine use other Python versions: do not touch them.
- Setup steps, expected download sizes and what not to install are in `docs/WORKFLOW.md`, section 2. Ask before installing anything and report sizes first.
- Scripts are faster, notebooks are easier to share and look at together. Explore in a notebook, then move working code into scripts.

## Pipeline contract (from `docs/WORKFLOW.md`, section 9)
One file per stage, so stages can be re-run and compared:
`keypoints_<model>.csv` -> `keypoints_<model>_filt.csv` -> `paddle.csv` -> `strokes.csv` -> `annotated.mp4` + plots.
- Timestamps come from the video's own frame times, not frame index or nominal fps.
- Raw model output is never modified. Filtering writes a separate file.
- One script per stage, driven by command-line arguments.

## Data
- Raw photos and clips live in `data/`, named `YYYY-MM-DD_<device>_<fps>fps_<what>_<take>.<ext>`. Never modify or delete them. Do not write outside `data/` without asking.
- Regenerable intermediate files go in `data/derived/` (create when first needed). Small results worth keeping (jitter and pixel-error tables, ffprobe outputs, hand labels) go in `test-logs/` with model or device and date in the name.
- Model weights go in `models/`. Large files (`data/`, `models/`, `.venv/`) are not for git.
- Raw data location is a per-project decision. Ask before changing it, and discuss how to handle intermediate steps before adding new ones.
- Never write device serial numbers or personal details into files or commits (`ME/` rule from the root).

## Documents
- `PLAN.md` (project root): always keep it current. Milestones with checklists, ticked as work happens. This is where we agree on the next step.
- `README.md`: findings, decisions, risks, open questions, dated log (YYYY-MM-DD). Mark each claim verified or assumed.
- `docs/`: everything else for planning and running the project. `docs/WORKFLOW.md` holds setup, recording protocol and commands. Create new documents here when needed.
- Note: this project keeps `WORKFLOW.md` in `docs/`, unlike `page-turner/`. After meaningful progress, update `PLAN.md`, `README.md` and, if commands changed, `docs/WORKFLOW.md`, then tell Sebastian what changed so he can ask the chat to sync the Project mirror.

## Coding standards
1. Use current library versions and idiomatic approaches.
2. Keep it simple. Do not over-engineer, no unnecessary defensive programming, no extra features.
3. Be concise. Keep the README minimal. No emojis, ever.
4. When something fails, find the root cause before changing anything. Do not guess: prove it with evidence, then fix the cause.
5. Measure instead of trusting demos. Save the raw numbers.

## Working style
- Small steps, one test at a time, say what to look for in each result.
- Use the brainstorming skill whenever we need to set or change a plan, and follow feature-dev guidelines for code generation (if either skill is not available in the session, say so and continue with a short written plan in `PLAN.md`).
- Use the agent-browser skill for online searches when needed.
- Git repository since 2026-11-16 (branch `main`, remote `origin` = private GitHub repo `zevaz13/pose-tracker` over SSH). Make small local commits with descriptive messages; Sebastian reviews and pushes. Never push or change remotes. `.gitignore` keeps `data/`, `models/` and `.venv/` out.
