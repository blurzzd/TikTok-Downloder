# TikTok Downloader

A desktop application with a simple graphical interface for downloading the publicly
available videos from a TikTok creator's profile. Built on top of
[yt-dlp](https://github.com/yt-dlp/yt-dlp), an actively maintained, open-source media
downloader.

## What it does

You enter a TikTok username or profile link, choose where to save the videos and what
format you want, and the app downloads every publicly available video from that
creator's profile. Downloads run in the background so the window never freezes, and you
get a live log, an overall progress bar, and a summary when it's done.

## Supported operating systems

- Windows 10 or 11
- macOS 12 or newer
- Linux (most modern distributions)

## Requirements

- Python 3.10 or newer (the setup scripts will help you install it if it's missing)
- FFmpeg, for audio-only downloads, video-only downloads, and combining separate
  audio/video streams (the setup scripts check for this and tell you how to install it
  if it's missing)
- An internet connection

You do not need to already know Python. The setup scripts handle installation and
configuration for you.

## Installing and setting up

1. Download this project as a ZIP from GitHub and extract it, or clone the repository.
2. Open the extracted folder.
3. Run the setup script for your operating system:
   - **Windows:** double-click `setup.bat`
   - **macOS/Linux:** open a terminal in the project folder and run `./setup.sh`
     (or `bash setup.sh`)

The setup script will:

- Check whether Python is installed and is a compatible version
- Offer to install Python automatically if it's missing (or give you manual
  installation instructions if automatic installation isn't possible)
- On Linux, create an isolated virtual environment (`venv`) so the app's dependencies
  never touch your system Python
- On macOS, install the app's dependency into your main Python environment
- Install the required Python packages
- Check whether FFmpeg is available and let you know if it isn't
- Create the default `saved videos` output folder
- Launch the application automatically once setup finishes

If setup fails partway through, it will explain what went wrong instead of failing
silently. You can safely run the setup script again after fixing the issue.

## Launching the app after setup

Once setup has completed at least once, you can start the app directly:

- **Windows:** double-click `run.bat`
- **macOS/Linux:** double-click `run.sh` if your file manager allows it, or run
  `./run.sh` from a terminal in the project folder

You will not need to type any Python commands for normal day-to-day use.

## Entering a TikTok creator

Type a username or paste a profile link into the input box. All of the following are
accepted:

- `https://www.tiktok.com/@username`
- `https://tiktok.com/@username`
- `https://www.tiktok.com/username`
- `tiktok.com/@username`
- `@username`
- `username`

If what you enter isn't recognizable as a TikTok username or profile link, the app
shows a clear error message instead of guessing.

## Download modes

- **Video only (no audio)** — the default. Downloads the video with its audio track
  removed.
- **Audio only** — extracts just the audio as an MP3 file.
- **Video with audio** — downloads the video with its original audio track intact.

## Quality

By default, the app downloads the best quality TikTok makes available for each video.
You can turn off "best available quality" to prefer a smaller file size instead, when a
lower-quality version is available. The app never claims a quality level that TikTok
doesn't actually offer for a given video — it simply asks yt-dlp for the best (or
smallest) of whatever formats TikTok provides.

## Where files are saved

If you don't choose a folder, videos are saved to a `saved videos` folder created next
to the application. You can choose a different folder at any time using the "Browse..."
button. Filenames are built from the creator's name, the video ID, and the video's
title, and are automatically sanitized so they work on Windows, macOS, and Linux. If a
file with the same name already exists, it won't be downloaded again — it's counted as
"skipped" instead of overwritten.

## FFmpeg

FFmpeg is a free, open-source tool used to extract audio, remove audio tracks, and
combine separate audio/video streams when needed. It is not bundled with this project.

- **Windows:** `winget install Gyan.FFmpeg`, or download from
  [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your PATH
- **macOS:** `brew install ffmpeg`
- **Linux:** install it with your distribution's package manager, e.g.
  `sudo apt-get install ffmpeg`

The setup scripts check for FFmpeg and let you know if it's missing. The app will also
show a clear error if you try to start a download without it.

## Troubleshooting

- **"Python was not found"** — run `setup.bat` or `setup.sh` again, or install Python
  manually from [python.org](https://www.python.org/downloads/).
- **"FFmpeg was not found on this computer"** — see the FFmpeg section above.
- **"That doesn't look like a valid TikTok username"** — double-check what you typed
  against the supported formats above.
- **"Couldn't load videos for this account"** — the account may not exist, may be
  private, or TikTok may be temporarily unavailable. Only public accounts can be
  downloaded.
- **A specific video fails to download** — the app logs the error and continues with
  the rest of the creator's videos. Check the log area for details.
- **Setup fails while installing packages** — check your internet connection and try
  running the setup script again.

## Limitations

- Only publicly available videos can be downloaded. This tool does not bypass logins,
  private-account restrictions, CAPTCHAs, or rate limits, and it will not attempt to.
- TikTok's site can change at any time, which may temporarily affect downloading until
  yt-dlp is updated. Keeping yt-dlp up to date (`pip install --upgrade yt-dlp` inside
  the project's virtual environment, or by re-running setup) usually resolves this.
- Very large profiles can take a while to download, since videos are downloaded one at
  a time.

## Responsible and legal use

Only download videos you own, have permission to use, or are otherwise legally entitled
to download and use. Respect TikTok's Terms of Service, applicable copyright law, and
the rights of individual creators. This tool is provided for personal, non-infringing
use such as archiving your own content or content you have explicit permission to save;
you are responsible for how you use it.

## Project structure

```
tiktok-downloader/
├── main.py            application entry point
├── downloader.py       download logic built on yt-dlp
├── gui.py              the Tkinter graphical interface
├── config.py            shared defaults and configuration
├── requirements.txt      Python dependencies
├── setup.bat / setup.sh   first-time setup scripts
├── run.bat / run.sh       everyday launchers
└── saved videos/          default download location
```
