import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp

import config


class TikTokDownloaderError(Exception):
    pass


class InvalidProfileError(TikTokDownloaderError):
    pass


class CreatorNotFoundError(TikTokDownloaderError):
    pass


class NoVideosFoundError(TikTokDownloaderError):
    pass


class FFmpegNotFoundError(TikTokDownloaderError):
    pass


class EventType(Enum):
    STATUS = "status"
    LOG = "log"
    PROGRESS = "progress"
    VIDEO_PROGRESS = "video_progress"
    ERROR = "error"
    FINISHED = "finished"


@dataclass
class DownloadSummary:
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    cancelled: bool = False


@dataclass
class ProgressEvent:
    type: EventType
    message: str = ""
    current: int = 0
    total: int = 0
    percent: float = 0.0
    level: str = "info"
    summary: DownloadSummary = None


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.]{1,24}$")


def normalize_profile_input(raw_input):
    if raw_input is None:
        raise InvalidProfileError("Please enter a TikTok username or profile link.")

    text = raw_input.strip().strip('"').strip("'")
    if not text:
        raise InvalidProfileError("Please enter a TikTok username or profile link.")

    lowered = text.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        parsed = urlparse(text)
        if "tiktok.com" not in parsed.netloc.lower():
            raise InvalidProfileError("That doesn't look like a TikTok link.")
        username = _extract_username_from_path(parsed.path)
    elif lowered.startswith("tiktok.com/") or lowered.startswith("www.tiktok.com/") or lowered in (
        "tiktok.com",
        "www.tiktok.com",
    ):
        parsed = urlparse(f"https://{text}")
        username = _extract_username_from_path(parsed.path)
    elif text.startswith("@"):
        username = text[1:]
    else:
        username = text

    username = username.strip("/ ")
    if not username:
        raise InvalidProfileError("Couldn't find a username in that input.")
    if not USERNAME_PATTERN.match(username):
        raise InvalidProfileError(f"'{username}' doesn't look like a valid TikTok username.")

    profile_url = f"https://www.tiktok.com/@{username}"
    return username, profile_url


def _extract_username_from_path(path):
    cleaned = path.strip("/")
    if not cleaned:
        raise InvalidProfileError("That link doesn't include a username.")
    first_segment = cleaned.split("/")[0]
    if first_segment.startswith("@"):
        first_segment = first_segment[1:]
    if not first_segment:
        raise InvalidProfileError("That link doesn't include a username.")
    return first_segment


def is_ffmpeg_available():
    return shutil.which("ffmpeg") is not None


def build_format_selector(mode, best_quality):
    primary_video = "bestvideo" if best_quality else "worstvideo"
    primary_audio = "bestaudio" if best_quality else "worstaudio"
    fallback = "best" if best_quality else "worst"

    if mode == config.DOWNLOAD_MODE_AUDIO_ONLY:
        return f"{primary_audio}/{fallback}"
    if mode == config.DOWNLOAD_MODE_VIDEO_ONLY:
        return f"{primary_video}/{fallback}"
    return f"{primary_video}+{primary_audio}/{fallback}"


def fetch_creator_videos(profile_url, username):
    options = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "ignoreerrors": False,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(profile_url, download=False)
    except yt_dlp.utils.DownloadError as error:
        raise CreatorNotFoundError(
            f"Couldn't load videos for @{username}. The account may not exist, "
            "may be private, or TikTok may be temporarily unavailable."
        ) from error

    if not info:
        raise CreatorNotFoundError(f"Couldn't find a TikTok creator named @{username}.")

    entries = [entry for entry in info.get("entries", []) if entry]
    videos = []
    for entry in entries:
        video_id = entry.get("id")
        url = entry.get("url") or entry.get("webpage_url")
        if not url and video_id:
            url = f"https://www.tiktok.com/@{username}/video/{video_id}"
        title = entry.get("title") or video_id or "video"
        if url:
            videos.append({"id": video_id, "url": url, "title": title})

    if not videos:
        raise NoVideosFoundError(f"@{username} doesn't have any publicly available videos to download.")

    return videos


def strip_audio_track(video_path):
    if not video_path.exists():
        return
    temp_path = video_path.with_name(video_path.stem + ".tmp" + video_path.suffix)
    command = ["ffmpeg", "-y", "-i", str(video_path), "-an", "-c:v", "copy", str(temp_path)]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0 or not temp_path.exists():
        if temp_path.exists():
            temp_path.unlink()
        raise TikTokDownloaderError("FFmpeg failed while removing the audio track from the video.")
    video_path.unlink()
    temp_path.rename(video_path)


def download_single_video(video, output_dir, mode, best_quality, progress_callback):
    format_selector = build_format_selector(mode, best_quality)
    outtmpl = str(output_dir / config.OUTPUT_FILENAME_TEMPLATE)

    base_options = {
        "format": format_selector,
        "outtmpl": outtmpl,
        "merge_output_format": config.MERGE_CONTAINER_FORMAT,
        "quiet": True,
        "no_warnings": True,
        "windowsfilenames": True,
        "trim_file_name": config.MAX_TRIMMED_FILENAME_LENGTH,
        "overwrites": False,
        "ignoreerrors": False,
        "noplaylist": True,
    }

    if mode == config.DOWNLOAD_MODE_AUDIO_ONLY:
        probe_options = dict(base_options)
        probe_options["skip_download"] = True
        try:
            with yt_dlp.YoutubeDL(probe_options) as probe_ydl:
                info = probe_ydl.extract_info(video["url"], download=False)
                predicted_path = Path(probe_ydl.prepare_filename(info)).with_suffix(f".{config.AUDIO_CODEC}")
        except yt_dlp.utils.DownloadError as error:
            raise TikTokDownloaderError(f"Could not read video information ({error})") from error
        if predicted_path.exists():
            return "skipped"

    options = dict(base_options)
    if mode == config.DOWNLOAD_MODE_AUDIO_ONLY:
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": config.AUDIO_CODEC,
            "preferredquality": config.AUDIO_QUALITY,
        }]

    progress_state = {"saw_downloading": False, "final_path": None}

    def hook(status):
        status_name = status.get("status")
        if status_name == "downloading":
            progress_state["saw_downloading"] = True
            downloaded = status.get("downloaded_bytes") or 0
            total_bytes = status.get("total_bytes") or status.get("total_bytes_estimate")
            if total_bytes:
                progress_callback(downloaded / total_bytes * 100)
        elif status_name == "finished":
            progress_state["final_path"] = status.get("filename")

    options["progress_hooks"] = [hook]

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([video["url"]])
    except yt_dlp.utils.DownloadError as error:
        raise TikTokDownloaderError(f"Download failed ({error})") from error

    if not progress_state["saw_downloading"]:
        return "skipped"

    if mode == config.DOWNLOAD_MODE_VIDEO_ONLY and progress_state["final_path"]:
        strip_audio_track(Path(progress_state["final_path"]))

    return "downloaded"


def run_download(profile_input, destination, mode, best_quality, event_queue, stop_event):
    def emit(event_type, **kwargs):
        event_queue.put(ProgressEvent(type=event_type, **kwargs))

    summary = DownloadSummary()
    try:
        username, profile_url = normalize_profile_input(profile_input)

        if not is_ffmpeg_available():
            raise FFmpegNotFoundError(
                "FFmpeg was not found on this computer. FFmpeg is required for audio-only "
                "downloads, video-only downloads, and combining separate audio/video streams. "
                "Install FFmpeg and make sure it is on your PATH, then try again."
            )

        output_dir = Path(destination) if destination else config.DEFAULT_OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        emit(EventType.STATUS, message=f"Looking up videos for @{username}...")
        emit(EventType.LOG, message=f"Looking up videos for @{username}...")

        videos = fetch_creator_videos(profile_url, username)
        total = len(videos)
        emit(EventType.STATUS, message=f"Found {total} video(s) for @{username}.")
        emit(EventType.LOG, message=f"Found {total} video(s) for @{username}.")

        for index, video in enumerate(videos, start=1):
            if stop_event.is_set():
                summary.cancelled = True
                emit(EventType.LOG, message="Download cancelled.")
                break

            title = video.get("title") or video.get("id") or "video"
            emit(EventType.STATUS, message=f"@{username} — video {index} of {total}: {title}")
            emit(EventType.PROGRESS, current=index - 1, total=total)

            def report_video_progress(percent, index=index, total=total):
                emit(EventType.VIDEO_PROGRESS, current=index, total=total, percent=percent)

            try:
                outcome = download_single_video(video, output_dir, mode, best_quality, report_video_progress)
                if outcome == "skipped":
                    summary.skipped += 1
                    emit(EventType.LOG, message=f"Skipped (already downloaded): {title}")
                else:
                    summary.downloaded += 1
                    emit(EventType.LOG, message=f"Downloaded: {title}")
            except TikTokDownloaderError as error:
                summary.failed += 1
                emit(EventType.LOG, message=f"Failed: {title} ({error})", level="error")
            except Exception as error:
                summary.failed += 1
                emit(EventType.LOG, message=f"Failed: {title} ({error})", level="error")

            emit(EventType.PROGRESS, current=index, total=total)

    except TikTokDownloaderError as error:
        emit(EventType.ERROR, message=str(error))
    except OSError as error:
        emit(EventType.ERROR, message=f"Couldn't create the destination folder: {error}")
    except Exception as error:
        emit(EventType.ERROR, message=f"Something unexpected went wrong: {error}")
    finally:
        emit(EventType.FINISHED, summary=summary)
