from pathlib import Path

APP_NAME = "TikTok Downloader"
APP_VERSION = "1.0.0"

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = BASE_DIR / "saved videos"

MIN_PYTHON_VERSION = (3, 10)

DOWNLOAD_MODE_VIDEO_ONLY = "video_only"
DOWNLOAD_MODE_AUDIO_ONLY = "audio_only"
DOWNLOAD_MODE_VIDEO_WITH_AUDIO = "video_with_audio"

DEFAULT_DOWNLOAD_MODE = DOWNLOAD_MODE_VIDEO_ONLY
DEFAULT_BEST_QUALITY = True

DOWNLOAD_MODE_OPTIONS = [
    (DOWNLOAD_MODE_VIDEO_ONLY, "Video only (no audio)"),
    (DOWNLOAD_MODE_AUDIO_ONLY, "Audio only"),
    (DOWNLOAD_MODE_VIDEO_WITH_AUDIO, "Video with audio"),
]

OUTPUT_FILENAME_TEMPLATE = "%(uploader)s_%(id)s_%(title).60s.%(ext)s"
MAX_TRIMMED_FILENAME_LENGTH = 150

AUDIO_CODEC = "mp3"
AUDIO_QUALITY = "192"
MERGE_CONTAINER_FORMAT = "mp4"
