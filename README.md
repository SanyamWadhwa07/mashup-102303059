# Mashup Project - 102303059

This project creates audio mashups from YouTube videos of a singer.

## Requirements

Make sure you have:
- Python 3.13+ installed
- Node.js installed (for yt-dlp JavaScript extraction)
- All Python packages installed: `pip install -r requirements.txt`

## Two Ways to Use

### Option 1: Command Line Tool

Run the command-line script:

```bash
python 102303059.py <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>
```

**Example:**
```bash
python 102303059.py "Arijit Singh" 15 25 output.wav
```

**Arguments:**
- `SingerName`: Name of the singer/artist to search for
- `NumberOfVideos`: Number of videos to download (must be > 10)
- `AudioDuration`: Duration in seconds to cut from each video (must be > 20)
- `OutputFileName`: Name of the output mashup file

### Option 2: Web Application

1. Start the Flask server:
```bash
python app.py
```

2. Open browser and go to: `http://127.0.0.1:5000`

3. Fill in the form:
   - Singer Name
   - Number of Videos (min 11)
   - Duration in seconds (min 21)
   - Your Email Address

4. Click Submit and wait for processing

5. Download link will appear when ready

6. Click "Send Mashup via Email" to send the download link to your email via EmailJS

## EmailJS Configuration

The web app uses EmailJS to send emails. Credentials are already configured:
- Public Key: s0qz07TFYkGJPw_7Z
- Service ID: service_asstztj
- Template ID: template_vpx

## Troubleshooting

**If you get "No module named..." errors:**
```bash
pip install -r requirements.txt
```

**If yt-dlp shows JavaScript runtime warnings:**
- Make sure Node.js is installed
- Verify: `node --version`
- Restart your terminal after installing Node.js

**If no mashup file is created:**
- Check the terminal for error messages
- Make sure you have an internet connection
- Try with a popular artist name

## Assignment Details

- Roll Number: 102303059
- Creates mashups by downloading YouTube videos
- Cuts specified duration from each video
- Merges them into a single audio file
- Web interface with email delivery via EmailJS
