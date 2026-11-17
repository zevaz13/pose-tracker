# M1 stills: shooting protocol

Shoot-day checklist for milestone M1 (Stage 0, stills). About 15 photos, one session of about 20 minutes. Written 2026-11-16, not yet run.

The photos answer three questions:
1. Do MediaPipe and RTMPose agree with each other?
2. Is either one right? Measured against tape markers.
3. How much do the numbers move when nothing changes (the noise floor)?

## Before the session
- [ ] Phone camera saves **JPG, not HEIF** (check the camera app settings).
- [ ] Phone transfer works: USB debugging on the phone (`adb devices` lists it), or USB file-transfer mode.
- [ ] Remote triggers the photo shutter (Volume Up). Fallback: the 10 s self-timer.
- [ ] Tape for markers: small, high-contrast dots, about 1.5 cm, in a color not on your clothes.
- [ ] Paddle.

## Setup (fixed for the whole session)
- **Lens and modes:** the main 1x camera, not the ultra-wide, which distorts angles near the edges. Portrait, beauty and AI-scene modes off. Default resolution, not the 50 MP mode.
- **Placement:** landscape, the same orientation as the later videos. Tripod at chest height (1.0-1.2 m), 3-4 m away. Whole body and paddle in frame, with margin on all sides.
- **Do not move the tripod** between shots. If it moves, note it and restart the noise-floor rows (5 and 6).
- **Light and background:** even light, no strong backlight (window behind you). Plain background, ideally the room where the videos will be recorded.
- **Clothes:** short sleeves and fitted clothes, so the elbow and knee are visible. Contrasting with the background.
- **Paddle:** hold it in every shot.

## Tape markers (ground truth)
Stick the dots on the side facing the camera:
- shoulder (acromion)
- elbow (lateral epicondyle)
- wrist (ulnar styloid)
- hip (greater trochanter)
- knee (lateral, at the joint line)
- ankle (lateral malleolus)

Clicking the dot centers later gives a measured 2D angle in the image plane, the same quantity the models output. A protractor held against the arm cannot be read precisely while holding the pose. For front-view shots (rows 3 and 4), add dots on the front of both shoulders and wrists if convenient. Leave the markers on for the whole session.

## Shot list

| # | View | Pose | Takes | Answers |
|---|---|---|---|---|
| 1 | side | ready position | 1 | baseline, easy pose |
| 2 | side | backhand contact, held | 1 | arm in front of the body |
| 3 | front | ready position | 1 | second viewpoint |
| 4 | front | backhand contact, held | 1 | arm crossing the torso (occlusion) |
| 5 | side | backhand contact, do not move, 5 shots in a row | 5 | model + image noise only |
| 6 | side | backhand contact, step out and back in each time | 5 | pose repeatability (compare with row 5) |

- **Side view:** the camera looks along the line through your shoulders; the arm moves across the image.
- **Front view:** the camera faces your chest.
- **Changing views:** turn your body, not the tripod. The camera stays fixed for the whole session.
- **Why rows 5 and 6:** a model run twice on the same image gives identical output, so jitter needs separate photos. Row 5 isolates sensor noise and tiny sway. Row 6 adds how well you reproduce the pose.
- **Optional extra:** one photo of a known length (e.g. a 1 m ruler or the paddle laid flat) in the stroke plane, for a pixel-to-cm scale.

## After the session
1. Copy the originals; never use messaging apps, which recompress:
   ```bash
   adb devices
   adb shell ls /sdcard/DCIM/Camera | tail -20
   adb pull /sdcard/DCIM/Camera/<file>.jpg data/
   ```
2. Rename in `data/` as `YYYY-MM-DD_phone_photo_<view>-<pose>_<take>.jpg`. `photo` replaces the fps field for stills. Examples:
   - `2026-11-17_phone_photo_side-ready_01.jpg`
   - `2026-11-17_phone_photo_front-backhand_01.jpg`
   - `2026-11-17_phone_photo_side-backhand-still_01.jpg` ... `_05` (row 5)
   - `2026-11-17_phone_photo_side-backhand-repeat_01.jpg` ... `_05` (row 6)
3. Write one line per session in `test-logs/stills-session-<date>.txt`: time, light (window/lamp), distance, camera height, lens, resolution, anything that went wrong.

## What to look for when we run the models (M1)
- Do the elbow, shoulder, trunk-lean and knee angles agree between models within a few degrees? How close are they to the angles measured from the markers?
- Is the wrist keypoint stable across rows 5 and 6?
- Do limbs get swapped or dropped when the arm crosses the body (row 4)?
