import os
import shutil
import srt
from moviepy import ImageClip, concatenate_videoclips, vfx
import moviepy.video.fx as fx
from datetime import timedelta

def generate_memorial_video(photos, music, subtitles, deceased_info, video_speed, subtitle_speeds, output_dir):
    """
    Generate memorial video components: Video (Visual only), Audio (Separate), Subtitles (Separate .srt)
    """
    
    # 1. Create Video From Photos (Visual Only)
    clips = []
    base_duration = 3.0 / video_speed # Base duration per photo adjusted by speed
    print(f"DEBUG: Processing {len(photos)} photos with video_speed={video_speed}, base_duration={base_duration}")
    
    for photo_path in photos:
        try:
            # Resize image to reasonable size (max 1920px) to prevent memory issues
            clip = ImageClip(photo_path)
            
            # Scale down if too large
            if clip.w > 1920 or clip.h > 1080:
                clip = clip.resized(height=1080) if clip.h > clip.w else clip.resized(width=1920)
            
            # CRITICAL: Apply duration AFTER resizing - ensure it's explicitly set
            clip = clip.with_duration(base_duration)
            
            # Add simple fade in/out using MoviePy 2.x syntax (Capitalized as suggested)
            try:
                clip = clip.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
            except Exception as ef:
                print(f"Effect application failed for {photo_path}, skipping effects: {ef}")
            
            clips.append(clip)
        except Exception as e:
            import traceback
            print(f"Error processing {photo_path}: {e}")
            traceback.print_exc()
            continue

    if not clips:
        # Check if photos exist at all
        missing = [p for p in photos if not os.path.exists(p)]
        raise ValueError(f"No valid clips created. Photos provided: {len(photos)}, Missing: {len(missing)}")

    final_video_clip = concatenate_videoclips(clips, method="compose")
    
    # Export Video (No Audio)
    video_output_path = os.path.join(output_dir, "video_only.mp4")
    final_video_clip.write_videofile(video_output_path, fps=24, codec="libx264", audio=False)
    
    # 2. Handle Audio Track (Separate)
    if music:
        audio_ext = os.path.splitext(music)[1]
        audio_output_path = os.path.join(output_dir, f"background_music{audio_ext}")
        shutil.copy(music, audio_output_path)
    
    # 3. Generate Subtitles File (.srt)
    srt_output_path = os.path.join(output_dir, "subtitles.srt")
    generate_srt(subtitles, deceased_info, base_duration, subtitle_speeds, len(photos), srt_output_path)

    # Clean up (Optional: Close clips)
    final_video_clip.close()
    for c in clips:
        c.close()

    return {
        'video': video_output_path,
        'audio': audio_output_path if music else None,
        'subtitles': srt_output_path
    }

def format_timedelta_to_srt(td):
    """Format timedelta to SRT timestamp format: HH:MM:SS,mmm"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def generate_srt(subtitle_source, deceased_info, base_duration, subtitle_speeds, num_photos, output_path):
    """
    Generate .srt file from segments with different speeds using srt-py library.
    """
    title_lines = []
    if deceased_info['name']:
        title_lines.append(f"故 {deceased_info['name']} 님을 기리며")
    if deceased_info['bio']:
        title_lines.extend([l.strip() for l in deceased_info['bio'].split('\n') if l.strip()])

    body_lines = []
    if subtitle_source and os.path.exists(subtitle_source):
        with open(subtitle_source, 'r', encoding='utf-8') as f:
            body_lines = [l.strip() for l in f.readlines() if l.strip()]

    ending_lines = []
    if deceased_info['user_bio']:
        ending_lines.extend([l.strip() for l in deceased_info['user_bio'].split('\n') if l.strip()])
    ending_lines.append("삼가 고인의 명복을 빕니다.")

    # Speed logic: 1.0x = 4 seconds per line base
    # (Higher speed = shorter time)
    BASE_LINE_TIME = 4.0
    
    segments = [
        ('title', title_lines, subtitle_speeds.get('title', 1.0)),
        ('body', body_lines, subtitle_speeds.get('body', 1.0)),
        ('ending', ending_lines, subtitle_speeds.get('ending', 1.0))
    ]

    total_video_duration = num_photos * base_duration
    subtitles = []
    current_time = timedelta(0)
    index = 1

    for seg_name, lines, speed in segments:
        line_duration = BASE_LINE_TIME / speed
        for line in lines:
            start = current_time
            end = start + timedelta(seconds=line_duration)

            # Cap at video duration
            if start.total_seconds() >= total_video_duration:
                break
            if end.total_seconds() > total_video_duration:
                end = timedelta(seconds=total_video_duration)

            subtitles.append(srt.Subtitle(
                index=index,
                start=start,
                end=end,
                content=line
            ))
            
            index += 1
            current_time = end
            
            if current_time.total_seconds() >= total_video_duration:
                break
        
        if current_time.total_seconds() >= total_video_duration:
            break

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt.compose(subtitles))

    print(f"DEBUG: SRT generated with {len(subtitles)} entries at {output_path}")
