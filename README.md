# ShutterSpeedAnalyzer

A Python tool to analyze high-speed video recordings of mechanical camera shutters to measure actual shutter speed accuracy.
I'm trying to test a Schneider-Kreuznach 90mm f8 Super-Angulon as well as the Zenit 11's shutter.

## Purpose

Mechanical shutters in film and older digital cameras can drift from their rated speeds over time. This tool helps diagnose shutter timing issues by:

1. Recording the shutter actuation with a high-speed camera pointed at a light source
2. Counting the number of frames where light is visible through the shutter
3. Calculating the actual exposure time and comparing it to the expected value

## Requirements

- Python 3.13+
- A high-speed camera capable of 180+ fps recording (tested with Canon R6 Mark II in 1080p HFR mode)
- A consistent light source (LED panel, phone screen, etc.)

## Installation

```bash
# Clone the repository
git clone https://github.com/user/ShutterSpeedAnalyzer.git
cd ShutterSpeedAnalyzer

# Install using uv
uv sync
```

## Usage

### Recording Test Videos

1. Set up a bright, consistent light source
2. Position your high-speed camera to record through the camera being tested
3. Set your recording camera to its highest frame rate (e.g., 180 fps)
4. Fire the shutter on the camera being tested while recording
5. Save the video file

### Running the Analyzer

```bash
uv run python src/shutterspeedanalyzer/analyzer.py
```

The tool will prompt for:
- Path to your video file
- The expected shutter speed (e.g., `1/60` or `1/125`)

### Example Output

```
--- Shutter Speed Analysis Setup ---
Camera Frame Rate (set): 180.00 fps (Assumes R6 II 1080p HFR)
Target Shutter Time: 1/60 (or 16.67 ms)
Expected Active Frames: 3.00 frames
----------------------------------------
| EVENT: Exposure start detected at Frame 45 (Brightness: 125.3)
| EVENT: Exposure end detected at Frame 48 (Brightness: 12.1)

--- Analysis Results ---
Frames counted as exposed: 3 frames
Actual Exposure Time: 16.67 ms
Nominal Exposure Time: 16.67 ms
Time Difference: +0.00 ms
Percentage Error: +0.00 %
Shutter Health Rating: GOOD (within +/-5%)
----------------------------------------
```

## Configuration

Edit the constants in `src/shutterspeedanalyzer/analyzer.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `CAMERA_FPS` | 180.0 | Frame rate of your recording camera |
| `BRIGHTNESS_THRESHOLD` | 18 | Minimum brightness (0-255) to detect light |
| `ROI_NORM` | (0.3, 0.3, 0.3, 0.3) | Region of interest as normalized coordinates |

## Interpreting Results

- **GOOD**: Within +/-5% of target - shutter is accurate
- **SLOW**: More than 5% over target - shutter stays open too long
- **FAST**: More than 5% under target - shutter closes too quickly

## License

MIT
