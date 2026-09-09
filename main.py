import sys
import tkinter as tk
from tkinter import messagebox


def main():
    try:
        import yt_dlp
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Missing dependency",
            "The yt-dlp package is not installed.\n\n"
            "Please run setup.bat (Windows) or setup.sh (macOS/Linux) again, "
            "then start the application using run.bat or run.sh.",
        )
        root.destroy()
        sys.exit(1)

    from gui import TikTokDownloaderApp

    app = TikTokDownloaderApp()
    app.run()


if __name__ == "__main__":
    main()
