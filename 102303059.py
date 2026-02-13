import sys
import os
import yt_dlp
import librosa
import soundfile as sf
import numpy as np

def create_mashup(singer, num_videos, duration, output_file):
    """
    Create a mashup of songs by downloading, cutting, and merging audio
    """
    print(f"Creating mashup for: {singer}")
    print(f"Number of videos: {num_videos}")
    print(f"Duration per video: {duration} seconds")
    
    # yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': False,
        'outtmpl': 'temp_%(id)s.%(ext)s',
        'noplaylist': True,
        'no_warnings': False,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }
    
    search_query = f"ytsearch{num_videos}:{singer}"
    combined_audio = None
    sr = 22050  # sample rate
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\nSearching YouTube for '{singer}'...")
            info = ydl.extract_info(search_query, download=False)
            entries = info.get('entries', [])[:num_videos]
            
            if not entries:
                print("Error: No videos found")
                return False
            
            print(f"Found {len(entries)} videos\n")
            
            for i, entry in enumerate(entries):
                try:
                    print(f"[{i+1}/{len(entries)}] Downloading: {entry.get('title', 'Unknown')}")
                    ydl.download([entry['webpage_url']])
                    
                    # Find downloaded file
                    exts = ['webm', 'm4a', 'mp3', 'mp4', 'opus']
                    file = None
                    for ext in exts:
                        candidate = f"temp_{entry['id']}.{ext}"
                        if os.path.exists(candidate):
                            file = candidate
                            break
                    
                    if not file:
                        print(f"  Warning: Downloaded file not found, skipping...")
                        continue
                    
                    # Load and cut audio
                    print(f"  Processing audio (cutting to {duration}s)...")
                    y, _ = librosa.load(file, sr=sr, mono=True, duration=duration)
                    
                    # Combine with previous audio
                    if combined_audio is None:
                        combined_audio = y
                    else:
                        combined_audio = np.concatenate((combined_audio, y))
                    
                    # Clean up temp file
                    os.remove(file)
                    print(f"  ✓ Successfully processed\n")
                    
                except Exception as e:
                    print(f"  Error processing video: {e}\n")
                    continue
            
            # Save final mashup
            if combined_audio is not None and len(combined_audio) > 0:
                print(f"Saving mashup to: {output_file}")
                sf.write(output_file, combined_audio, sr)
                print(f"✓ Mashup created successfully!")
                return True
            else:
                print("Error: No audio was combined")
                return False
                
    except Exception as e:
        print(f"Fatal error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python 102303059.py <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>")
        sys.exit(1)
    
    singer = sys.argv[1]
    try:
        num_videos = int(sys.argv[2])
        duration = int(sys.argv[3])
    except ValueError:
        print("Error: NumberOfVideos and AudioDuration must be integers")
        sys.exit(1)
    
    if num_videos <= 10:
        print("Error: NumberOfVideos must be greater than 10")
        sys.exit(1)
    
    if duration <= 20:
        print("Error: AudioDuration must be greater than 20")
        sys.exit(1)
    
    output = sys.argv[4]
    
    # Create the mashup
    success = create_mashup(singer, num_videos, duration, output)
    
    if not success:
        print("\nMashup creation failed!")
        sys.exit(1)
    else:
        sys.exit(0)
