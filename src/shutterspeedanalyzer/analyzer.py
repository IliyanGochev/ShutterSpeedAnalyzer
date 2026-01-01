import cv2
import numpy as np
import os
from pathlib import Path

# --- Configuration Constants ---
# Use the closest rounded number for simplicity in calculations.
# The Canon R6 Mark II's High Frame Rate for Full HD is 179.82 fps.
CAMERA_FPS = 180.0 

# Threshold for detecting light: The minimum average brightness (0-255) 
# required in the ROI to consider the shutter "open" and the frame "active".
# You may need to adjust this based on your light source and setup.
BRIGHTNESS_THRESHOLD = 45

# Region of Interest (ROI) for analysis: 
# We focus on the central area where the shutter opening is most uniform.
# These values are normalized (0.0 to 1.0) relative to the frame size.
# x_start, y_start, width, height
ROI_NORM = (0.3, 0.3, 0.3, 0.3) 

def analyze_shutter_video(video_path, target_shutter_speed_str):
    """
    Analyzes a high-speed video recording of a shutter opening to determine 
    the actual exposure time by counting illuminated frames.

    Args:
        video_path (str): Path to the input video file.
        target_shutter_speed_str (str): The nominal shutter speed (e.g., '1/60').
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at '{video_path}'")
        return

    # 1. Video and Target Setup
    
    # Calculate target time in seconds from the input string (e.g., '1/60' -> 0.01667s)
    try:
        if '/' in target_shutter_speed_str:
            num, den = map(int, target_shutter_speed_str.split('/'))
            target_time_s = num / den
        elif '.' in target_shutter_speed_str:
            target_time_s = float(target_shutter_speed_str)
        else:
            target_time_s = 1.0 / int(target_shutter_speed_str)
        
        target_frames = target_time_s * CAMERA_FPS

    except ValueError:
        print(f"Error: Invalid shutter speed format '{target_shutter_speed_str}'. Please use format '1/X' or a decimal value.")
        return

    print("\n--- Shutter Speed Analysis Setup ---")
    print(f"Camera Frame Rate (set): {CAMERA_FPS:.2f} fps (Assumes R6 II 1080p HFR)")
    print(f"Target Shutter Time: {target_shutter_speed_str} (or {target_time_s*1000:.2f} ms)")
    print(f"Expected Active Frames: {target_frames:.2f} frames")
    print("-" * 40)
    
    # Initialize video capture
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file '{video_path}'")
        return

    # Get video dimensions to calculate the concrete ROI
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Calculate pixel coordinates for the ROI
    x_start = int(frame_width * ROI_NORM[0])
    y_start = int(frame_height * ROI_NORM[1])
    roi_w = int(frame_width * ROI_NORM[2])
    roi_h = int(frame_height * ROI_NORM[3])
    
    # Variables for tracking the exposure event
    total_frames = 0
    active_frames = 0
    in_exposure = False

    # 2. Frame Processing Loop
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            total_frames += 1
            
            # Convert frame to grayscale for simpler brightness analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Extract the Region of Interest (ROI)
            roi = gray[y_start : y_start + roi_h, x_start : x_start + roi_w]
            
            # Calculate the average brightness of the ROI
            avg_brightness = np.mean(roi)
            
            # Check if the shutter is currently 'open' based on the brightness threshold
            is_light_visible = avg_brightness >= BRIGHTNESS_THRESHOLD
            
            # --- State Machine Logic for Exposure Detection ---
            if is_light_visible and not in_exposure:
                # Start of exposure detected
                in_exposure = True
                active_frames = 1
                # Optional: print event to console
                print(f"| EVENT: Exposure start detected at Frame {total_frames} (Brightness: {avg_brightness:.1f})")

            elif is_light_visible and in_exposure:
                # Still within exposure
                active_frames += 1
                
            elif not is_light_visible and in_exposure:
                # End of exposure detected
                in_exposure = False
                # Optional: print event to console
                print(f"| EVENT: Exposure end detected at Frame {total_frames} (Brightness: {avg_brightness:.1f})")
                
                # We break after the first full exposure event is finished.
                break

            # --- Visual Debug (Optional) ---
            # You can uncomment this section to see the live video feed 
            # and the ROI being analyzed. Press 'q' to stop early.
            
            # frame_display = frame.copy()
            # color = (0, 255, 0) if is_light_visible else (0, 0, 255)
            # cv2.rectangle(frame_display, (x_start, y_start), (x_start + roi_w, y_start + roi_h), color, 2)
            # cv2.putText(frame_display, f"B: {avg_brightness:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            # cv2.putText(frame_display, f"Frames: {active_frames}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            # cv2.imshow('Shutter Analysis Feed', frame_display)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
            
    finally:
        # Release resources
        cap.release()
        cv2.destroyAllWindows()

    # 3. Calculation and Results

    if active_frames > 0:
        actual_time_s = active_frames / CAMERA_FPS

        # Calculate the relative error
        time_difference = actual_time_s - target_time_s
        percentage_error = (time_difference / target_time_s) * 100

        # Determine the speed rating for display
        if percentage_error > 5:
            rating = "SLOW (needs adjustment)"
        elif percentage_error < -5:
            rating = "FAST (needs adjustment)"
        else:
            rating = "GOOD (within +/-5%)"

        print("\n--- Analysis Results ---")
        print(f"Frames counted as exposed: {active_frames} frames")
        print(f"Actual Exposure Time: {actual_time_s*1000:.2f} ms")
        print(f"Nominal Exposure Time: {target_time_s*1000:.2f} ms")
        print(f"Time Difference: {time_difference*1000:+.2f} ms")
        print(f"Percentage Error: {percentage_error:+.2f} %")
        print(f"Shutter Health Rating: {rating}")
        print("-" * 40)

        return {
            'active_frames': active_frames,
            'actual_time_s': actual_time_s,
            'target_time_s': target_time_s,
            'percentage_error': percentage_error,
            'success': True
        }

    else:
        print("\n--- Analysis Failed ---")
        print("No exposure detected (0 frames counted). Check the following:")
        print(f"1. Is the video file correct and does it show the light? ")
        print(f"2. Is the BRIGHTNESS_THRESHOLD ({BRIGHTNESS_THRESHOLD}) too high? Try lowering it.")
        print("3. Is the light source bright enough?")
        print("-" * 40)

        return {'success': False}


def batch_analyze_samples(samples_dir='samples'):
    """
    Batch processes all videos in the samples directory structure.
    Each subfolder name represents the shutter speed denominator (e.g., '60' means 1/60).

    Args:
        samples_dir (str): Path to the samples directory containing subfolders.
    """
    samples_path = Path(samples_dir)

    if not samples_path.exists():
        print(f"Error: Samples directory '{samples_dir}' not found.")
        return

    # Supported video extensions
    video_extensions = {'.mp4', '.MP4', '.mov', '.MOV', '.avi', '.AVI'}

    # Get all subdirectories sorted by shutter speed denominator (numerically)
    subfolders = [d for d in samples_path.iterdir() if d.is_dir()]

    # Sort numerically by folder name
    try:
        subfolders.sort(key=lambda x: int(x.name))
    except ValueError:
        # If some folders aren't numeric, sort alphabetically
        subfolders.sort(key=lambda x: x.name)

    total_videos = 0
    processed_videos = 0
    speed_results = {}  # Store results per shutter speed

    print("=" * 60)
    print("BATCH SHUTTER SPEED ANALYSIS")
    print("=" * 60)
    print(f"Camera Frame Rate: {CAMERA_FPS:.2f} fps (Canon R6 II 1080p HFR)")
    print(f"Brightness Threshold: {BRIGHTNESS_THRESHOLD}")
    print(f"ROI (normalized): {ROI_NORM}")
    print("=" * 60)

    # Process each subfolder
    for subfolder in subfolders:
        shutter_denominator = subfolder.name

        # Get all video files in this subfolder
        video_files = [f for f in subfolder.iterdir()
                      if f.is_file() and f.suffix in video_extensions]

        if not video_files:
            print(f"\nSkipping folder '{shutter_denominator}' - no video files found.")
            continue

        total_videos += len(video_files)

        print(f"\n{'='*60}")
        print(f"SHUTTER SPEED: 1/{shutter_denominator}")
        print(f"Videos found: {len(video_files)}")
        print(f"{'='*60}")

        # Store results for this shutter speed
        speed_results[shutter_denominator] = []

        # Process each video in this folder
        for video_file in sorted(video_files):
            print(f"\n>>> Processing: {video_file.name}")
            target_speed_str = f"1/{shutter_denominator}"

            try:
                result = analyze_shutter_video(str(video_file), target_speed_str)
                if result and result.get('success'):
                    speed_results[shutter_denominator].append(result)
                    processed_videos += 1
            except Exception as e:
                print(f"!!! Error processing {video_file.name}: {str(e)}")

    # Summary
    print("\n" + "=" * 60)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Total videos found: {total_videos}")
    print(f"Successfully processed: {processed_videos}")
    print(f"Failed: {total_videos - processed_videos}")
    print("=" * 60)

    # Print summary report
    print("\n" + "=" * 60)
    print("SUMMARY REPORT - AVERAGE RESULTS PER SHUTTER SPEED")
    print("=" * 60)

    for shutter_denominator in sorted(speed_results.keys(), key=lambda x: int(x)):
        results = speed_results[shutter_denominator]

        if not results:
            continue

        # Calculate averages
        avg_frames = sum(r['active_frames'] for r in results) / len(results)
        avg_actual_time = sum(r['actual_time_s'] for r in results) / len(results)
        avg_target_time = results[0]['target_time_s']  # Same for all in this group
        avg_percentage_error = sum(r['percentage_error'] for r in results) / len(results)

        # Determine rating
        if avg_percentage_error > 5:
            rating = "SLOW"
        elif avg_percentage_error < -5:
            rating = "FAST"
        else:
            rating = "GOOD"

        print(f"\n1/{shutter_denominator} ({len(results)} videos)")
        print(f"  Avg Frames: {avg_frames:.1f}")
        print(f"  Avg Actual Time: {avg_actual_time*1000:.2f} ms")
        print(f"  Target Time: {avg_target_time*1000:.2f} ms")
        print(f"  Avg Error: {avg_percentage_error:+.2f}%")
        print(f"  Rating: {rating}")

    print("=" * 60)


if __name__ == '__main__':
    print("Welcome to the Shutter Speed Video Analyzer!")
    print("Ensure your videos were shot in Canon R6 II 1080p HFR (approx. 180 fps).")
    print()

    # Check if we should run in batch mode
    mode = input("Mode? (1=Single video, 2=Batch process samples folder) [2]: ").strip()

    if mode == '1':
        # Single video mode (original behavior)
        video_file = input("Enter the path to your video file (e.g., 'shutter_test.mp4'): ")
        target_speed = input("Enter the set shutter speed (e.g., '1/60' or '1/125'): ")
        analyze_shutter_video(video_file, target_speed)
    else:
        # Batch mode (default)
        samples_dir = input("Enter samples directory path [samples]: ").strip()
        if not samples_dir:
            samples_dir = 'samples'
        batch_analyze_samples(samples_dir)