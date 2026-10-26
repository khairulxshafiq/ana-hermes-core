#!/usr/bin/env python3
"""
Convert horizontal video to vertical 9:16 short with blurred background & overlays.
Usage: python3 render_vertical_short.py input.mov output_9x16.mp4 "TITLE" "SUBTITLE" "FOOTER QUOTE"
"""
import sys
import subprocess

def render_vertical(input_path, output_path, title, subtitle="", quote=""):
    filters = [
        "[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,boxblur=20:5[bg]",
        "[0:v]scale=720:-1[fg]",
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[base]"
    ]
    
    text_filters = []
    if title:
        text_filters.append(f"drawtext=text='{title}':fontcolor=white:fontsize=36:box=1:boxcolor=black@0.6:boxborderw=10:x=(w-text_w)/2:y=180")
    if subtitle:
        text_filters.append(f"drawtext=text='{subtitle}':fontcolor=yellow:fontsize=24:box=1:boxcolor=black@0.6:boxborderw=8:x=(w-text_w)/2:y=240")
    if quote:
        text_filters.append(f"drawtext=text='{quote}':fontcolor=white:fontsize=26:box=1:boxcolor=black@0.7:boxborderw=10:x=(w-text_w)/2:y=1050")
    
    if text_filters:
        filters.append(f"[base]{','.join(text_filters)}[v]")
        video_map = "[v]"
    else:
        video_map = "[base]"
        
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", ";".join(filters),
        "-map", video_map,
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Error during render:", res.stderr)
        sys.exit(res.returncode)
    print("Render completed successfully:", output_path)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: render_vertical_short.py <input> <output> <title> [subtitle] [quote]")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2]
    t = sys.argv[3] if len(sys.argv) > 3 else ""
    s = sys.argv[4] if len(sys.argv) > 4 else ""
    q = sys.argv[5] if len(sys.argv) > 5 else ""
    render_vertical(inp, out, t, s, q)
