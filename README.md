# Triple T — WRO Future Engineers 2026

This repository documents Team Triple T's entry for the WRO Future Engineers 2026 competition. It will contain the team's engineering journal, source code, mechanical and electrical designs, testing evidence, and instructions needed to reproduce the autonomous vehicle.

## Team

### Members

- Tuy Caroline
- Thavrak Bunn Raksa
- Lim Anita

### Coach

- Lean Ratana

### Team photo

![Team Triple T](media/team-triple-t.jpg)

## Competition

- **Category:** WRO Future Engineers
- **Country:** Cambodia
- **Organizer:** STEM Cambodia
- **Competition date:** September 5, 2026
- **Documentation deadline:** August 28, 2026

## Current vehicle design

### Computing and software

- **Main controller:** Raspberry Pi 5 Model B Rev 1.1 with 4 GB RAM
- **Operating system:** Raspberry Pi OS based on Debian GNU/Linux 13 (64-bit)
- **Programming language:** Python 3.13.5
- **Vision library:** OpenCV 4.10.0
- **Other core libraries:** NumPy 2.2.4, gpiozero 2.0.1, lgpio 0.2.2.0
- **Camera interface:** V4L2/UVC fallback because `pyrealsense2` is not installed

The Raspberry Pi performs perception and control on the vehicle. It reads the RealSense color and depth streams, applies OpenCV color segmentation, and sends steering and drive commands through its GPIO pins. Processing is performed locally so the vehicle does not depend on wireless communication while driving.

### Mobility and mechanical design

- **Chassis and steering geometry:** Ackermann steering
- **Motor driver:** L298N
- **Steering servo:** MG90S
- **Drive motors:** Two DC motors; exact model to be documented
- **Driven axle:** Rear
- **Steered axle:** Front
- **Vehicle dimensions and weight:** To be measured
- **Wheel size and gear ratio:** To be measured

The front wheels are turned by a servo using an Ackermann-style linkage, while the rear wheels provide propulsion. Both rear motors are currently connected in parallel to one L298N output channel. The team must verify compliance with WRO rule 11.13 because two motors must not independently drive separate wheels unless the drive wheels are mechanically connected.

### Sensors and perception

- **Camera:** Intel RealSense D435i
- **Other sensors:** None
- **Pillar detection:** OpenCV color detection is used to distinguish red and green pillars.

The camera provides a 640 × 480 color stream and a 640 × 480 depth stream. The current software uses RGB and depth but does not use the camera's IMU. Color frames are converted from BGR to HSV. Masks are cleaned with morphological opening and closing before external contours are selected. Contours smaller than 300 pixels are rejected. Distance is estimated from the median valid depth inside an 11 × 11 area around a detected contour's center.

The current HSV settings are red at hue 178 ± 10, green at hue 59 ± 20, blue at hue 110 ± 15, and dark blue at hue 115 ± 15. Saturation and brightness limits are also applied. Calibration scripts allow the team to sample colors and adjust thresholds for the lighting at the competition venue.

### Navigation strategy

The project currently contains two separate experimental driving approaches:

1. `steer_by_color.py` searches the full image for red, green, and dark-blue contours. It drives forward, applies a fixed steering angle when a nearby red or green object is detected, and stops when dark blue is detected within 500 mm.
2. `line_follow.py` examines two 80-pixel-wide vertical regions at the left and right edges of the camera image. It combines dark-blue and black masks and turns toward the side that loses the detected line. A region is considered to contain the line when at least 3% of its pixels match.

These are reactive prototypes rather than a complete competition state machine. There is currently no implemented lap counter, clockwise/counterclockwise mode, finish-section behavior, complete obstacle-round strategy, or validated side-obedience sequence.

The parking strategy has not yet been implemented.

### Power system and current issue

- **Available battery voltage:** 12 V
- **Current issue:** A portable regulated power supply for the Raspberry Pi 5 is not yet available.

The Raspberry Pi 5 cannot be powered directly from the 12 V battery. A suitable regulated supply and a complete power-distribution design are still required.

The documented GPIO connections are:

- GPIO18: steering-servo signal
- GPIO23: L298N IN1
- GPIO24: L298N IN2
- GPIO12: L298N ENA
- Physical pin 2: 5 V for the steering servo
- Physical pins 14 and 20: common ground
- L298N OUT1/OUT2: both rear motors wired in parallel
- RealSense D435i: USB connection to the Raspberry Pi

The 12 V battery currently supplies the motor driver. The Raspberry Pi uses a separate USB-C power supply during development. Battery capacity, measured current consumption, peak motor current, and regulator specifications are not yet available, so a verified power budget cannot yet be calculated.

## Software architecture

The robot project currently exists at `/home/aaron/robot_car` on the Raspberry Pi. The important observed programs are:

- `steer_by_color.py`: current reactive color-steering program and likely main experimental entry point
- `line_follow.py`: border-region line-following experiment
- `color_detection.py`: shared HSV masking, contour detection, depth lookup, and calibration tools
- `depth_camera.py`: custom V4L2 Z16 depth-stream reader
- `color_probe.py` and `color_sample.py`: HSV calibration helpers
- `test_car.py` and `test_car_gui.py`: motor and servo hardware tests
- `drive_terminal.py`: manual keyboard control for hardware verification
- `human_detection.py`: experimental HOG person detection that is not connected to driving

On startup, the color-steering program opens the camera, enables automatic color settings, starts a background depth reader, and then processes each color frame. Detected contours and depth measurements are passed to the decision logic. The decision logic commands the L298N through gpiozero and sets the servo angle. Shutdown logic stops the motor, centers the servo, releases the camera, and stops the depth thread.

The current control is bang-bang rather than proportional. Motor speed is either forward or stopped, and steering uses fixed angles instead of PID control. If red and green are detected simultaneously within the distance threshold, red receives priority because its condition is evaluated first. If depth becomes unavailable, the current color-steering program cannot satisfy its distance conditions; a fail-safe stop must be added before competition use.

One file, `autonomous_drive.py`, was found to contain only NUL bytes and is not functional. It is not being presented as working competition code.

## Engineering process and current evidence

The code shows several iterations and engineering responses:

- The team developed a V4L2 camera fallback after `pyrealsense2` was unavailable.
- A custom memory-mapped Z16 reader was created because OpenCV could not directly read the RealSense depth node.
- Calibration tools and adjustable HSV trackbars were added to tune colors under different lighting.
- Morphological filtering, a minimum contour area, and median depth sampling were introduced to reduce noisy detections.
- Different fixed steering angles exist in the color-steering and line-following experiments, showing that behavior-specific steering values have been tested.
- Camera and GPIO cleanup in `finally` blocks provides safer shutdown after an error or manual stop.

However, no dated test logs, measured success rates, lap times, detection accuracy, processing frame rate, motor-current measurements, or calibration result files were found. These observations therefore document software evolution but do not yet prove performance improvement.

The most important known failure modes are loss of depth data, false color detection caused by lighting, inconsistent servo-angle conventions between scripts, insufficient portable power, and the corrupt autonomy file. Proposed mitigations must be tested before they can be described as completed improvements.

## Testing workflow

The existing hardware tests sweep the steering servo and test motor movement in both directions. The calibration tools display or print sampled HSV values. Before final evaluation, the team should record repeatable evidence from at least ten autonomous runs, including completion rate, lap time, steering failures, false pillar detections, processing frame rate, CPU temperature, and battery behavior.

The following measurements are still required:

- Vehicle length, width, height, and total weight
- Wheel diameter, wheelbase, track width, and motor gear ratio
- Battery capacity and regulator ratings
- Idle, normal, peak, and stalled current
- Color-detection performance under multiple lighting conditions
- Depth accuracy compared with a tape-measured distance
- Autonomous lap success rate and timing
- Parking success rate after parking is implemented

## Reproducing the current prototype

The current prototype is run manually from `/home/aaron/robot_car` using the Python virtual environment:

```bash
robot_env/bin/python steer_by_color.py
robot_env/bin/python line_follow.py
robot_env/bin/python color_detection.py
```

The Raspberry Pi, RealSense camera, motor driver, servo, motors, and battery must be connected according to the documented GPIO map and share the required common ground. The Raspberry Pi must receive regulated power through an appropriate USB-C supply and must never receive 12 V directly.

Full reproduction is not yet possible from this GitHub repository because the source files, dependency manifest, exact motor specification, CAD files, dimensioned mechanical drawing, measured power budget, and calibration data have not yet been uploaded.

## Detailed robot audit

The complete read-only technical inspection, including wiring diagrams, state diagrams, exact thresholds, file inventory, risk analysis, and rubric gap assessment, is available in [docs/WRO_ROBOT_AUDIT.md](docs/WRO_ROBOT_AUDIT.md).

## Engineering journal PDF

The evidence-based project report is available as [Triple_T_Engineering_Journal.pdf](docs/Triple_T_Engineering_Journal.pdf). Its editable source is [ENGINEERING_JOURNAL.md](docs/ENGINEERING_JOURNAL.md).

To regenerate the PDF:

```bash
python3 -m pip install -r requirements-docs.txt
python3 scripts/build_report.py
```

## Vehicle photographs

### Side view 1

![Vehicle side view 1](media/vehicle-side-view-1.jpg)

### Front view

![Vehicle front view](media/vehicle-front-view.jpg)

### Rear and electronics view

![Vehicle rear and electronics view](media/vehicle-rear-view.jpg)

### Top view

![Vehicle top view](media/vehicle-top-view.jpg)

### Side view 2

![Vehicle side view 2](media/vehicle-side-view-2.jpg)

A bottom-view photograph is still required to complete the WRO vehicle photo set.

## Documentation status

The engineering documentation is currently in progress. Technical details, source code, diagrams, photographs, CAD files, test results, and autonomous-driving videos will be added as they become available.

## Planned documentation

- Mobility and mechanical design
- Power and sensor architecture
- Software architecture and obstacle strategy
- Systems thinking and engineering decisions
- Assembly and reproduction instructions
- Engineering journal
- Testing workflow and results
- Vehicle and team photographs
- Open Challenge and Obstacle Challenge videos

