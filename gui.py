import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import config
import downloader


class TikTokDownloaderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(config.APP_NAME)
        self.root.geometry("760x660")
        self.root.minsize(680, 580)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.destination_var = tk.StringVar(value=str(config.DEFAULT_OUTPUT_DIR))
        self.mode_var = tk.StringVar(value=config.DEFAULT_DOWNLOAD_MODE)
        self.best_quality_var = tk.BooleanVar(value=config.DEFAULT_BEST_QUALITY)
        self.status_var = tk.StringVar(value="Ready.")

        self.event_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread = None

        self._build_widgets()
        self._poll_queue()

    def run(self):
        self.root.mainloop()

    def _build_widgets(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)

        title_label = ttk.Label(outer, text=config.APP_NAME, font=("TkDefaultFont", 16, "bold"))
        title_label.pack(anchor="w", pady=(0, 12))

        input_frame = ttk.Frame(outer)
        input_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(input_frame, text="TikTok creator (username or profile link):").pack(anchor="w")
        self.profile_entry = ttk.Entry(input_frame)
        self.profile_entry.pack(fill="x", pady=(4, 0))
        self.profile_entry.bind("<Return>", lambda event: self._start_download())
        self.profile_error_label = ttk.Label(input_frame, text="", foreground="#b3261e")
        self.profile_error_label.pack(anchor="w", pady=(2, 0))

        dest_frame = ttk.Frame(outer)
        dest_frame.pack(fill="x", pady=(8, 8))
        ttk.Label(dest_frame, text="Save videos to:").pack(anchor="w")
        dest_row = ttk.Frame(dest_frame)
        dest_row.pack(fill="x", pady=(4, 0))
        self.destination_entry = ttk.Entry(dest_row, textvariable=self.destination_var)
        self.destination_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(dest_row, text="Browse...", command=self._browse_folder).pack(side="left", padx=(8, 0))

        options_frame = ttk.Frame(outer)
        options_frame.pack(fill="x", pady=(8, 8))

        mode_frame = ttk.LabelFrame(options_frame, text="Download mode", padding=8)
        mode_frame.pack(side="left", fill="both", expand=True)
        for value, label in config.DOWNLOAD_MODE_OPTIONS:
            ttk.Radiobutton(mode_frame, text=label, value=value, variable=self.mode_var).pack(anchor="w")

        quality_frame = ttk.LabelFrame(options_frame, text="Quality", padding=8)
        quality_frame.pack(side="left", fill="both", expand=True, padx=(8, 0))
        ttk.Checkbutton(
            quality_frame,
            text="Download best available quality",
            variable=self.best_quality_var,
        ).pack(anchor="w")
        ttk.Label(
            quality_frame,
            text="Turn off to prefer a smaller file size when available.",
            foreground="#5f6368",
            font=("TkDefaultFont", 8),
            wraplength=220,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        action_frame = ttk.Frame(outer)
        action_frame.pack(fill="x", pady=(8, 8))
        self.start_button = ttk.Button(action_frame, text="Start Download", command=self._start_download)
        self.start_button.pack(side="left")
        self.cancel_button = ttk.Button(action_frame, text="Cancel", command=self._cancel_download, state="disabled")
        self.cancel_button.pack(side="left", padx=(8, 0))

        progress_frame = ttk.Frame(outer)
        progress_frame.pack(fill="x", pady=(8, 8))
        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate", maximum=100)
        self.progress_bar.pack(fill="x")
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack(anchor="w", pady=(4, 0))

        status_label = ttk.Label(outer, textvariable=self.status_var, font=("TkDefaultFont", 10, "italic"))
        status_label.pack(anchor="w", pady=(0, 8))

        log_frame = ttk.LabelFrame(outer, text="Log", padding=8)
        log_frame.pack(fill="both", expand=True)
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side="right", fill="y")
        self.log_text = tk.Text(log_frame, height=10, wrap="word", yscrollcommand=log_scroll.set, state="disabled")
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)

    def _browse_folder(self):
        initial_dir = self.destination_var.get() or str(config.DEFAULT_OUTPUT_DIR)
        selected = filedialog.askdirectory(initialdir=initial_dir, title="Choose a destination folder")
        if selected:
            self.destination_var.set(selected)

    def _start_download(self):
        if self.worker_thread and self.worker_thread.is_alive():
            return

        self.profile_error_label.config(text="")
        raw_profile = self.profile_entry.get().strip()
        try:
            downloader.normalize_profile_input(raw_profile)
        except downloader.InvalidProfileError as error:
            self.profile_error_label.config(text=str(error))
            return

        destination = self.destination_var.get().strip() or str(config.DEFAULT_OUTPUT_DIR)
        mode = self.mode_var.get()
        best_quality = self.best_quality_var.get()

        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

        self.progress_bar.config(value=0)
        self.progress_label.config(text="")
        self._set_status("Starting...")

        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(
            target=downloader.run_download,
            args=(raw_profile, destination, mode, best_quality, self.event_queue, self.stop_event),
            daemon=True,
        )
        self.worker_thread.start()

        self.start_button.config(state="disabled")
        self.cancel_button.config(state="normal")

    def _cancel_download(self):
        self.stop_event.set()
        self.cancel_button.config(state="disabled")
        self._set_status("Cancelling... finishing the current video.")

    def _poll_queue(self):
        try:
            while True:
                event = self.event_queue.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _handle_event(self, event):
        if event.type == downloader.EventType.STATUS:
            self._set_status(event.message)
        elif event.type == downloader.EventType.LOG:
            self._append_log(event.message, event.level)
        elif event.type == downloader.EventType.PROGRESS:
            percent = (event.current / event.total * 100) if event.total else 0
            self.progress_bar.config(value=percent)
            self.progress_label.config(text=f"{event.current} of {event.total} videos completed")
        elif event.type == downloader.EventType.VIDEO_PROGRESS:
            self.progress_label.config(
                text=f"Video {event.current} of {event.total} — downloading ({event.percent:.0f}%)"
            )
        elif event.type == downloader.EventType.ERROR:
            self._append_log(event.message, "error")
            messagebox.showerror("Error", event.message)
        elif event.type == downloader.EventType.FINISHED:
            self._on_finished(event.summary)

    def _on_finished(self, summary):
        self.start_button.config(state="normal")
        self.cancel_button.config(state="disabled")

        had_activity = summary.downloaded or summary.skipped or summary.failed or summary.cancelled
        if not had_activity:
            self._set_status("Ready.")
            return

        self._set_status("Download cancelled." if summary.cancelled else "Download complete.")

        message = (
            f"Downloaded: {summary.downloaded}\n"
            f"Skipped (already had them): {summary.skipped}\n"
            f"Failed: {summary.failed}"
        )
        if summary.cancelled:
            message += "\n\nThe download was cancelled before all videos were processed."

        self._append_log(
            f"Finished. Downloaded {summary.downloaded}, skipped {summary.skipped}, failed {summary.failed}."
        )
        messagebox.showinfo("Download summary", message)

    def _append_log(self, message, level="info"):
        self.log_text.config(state="normal")
        prefix = "[!] " if level == "error" else ""
        self.log_text.insert(tk.END, f"{prefix}{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _set_status(self, message):
        self.status_var.set(message)

    def _on_close(self):
        if self.worker_thread and self.worker_thread.is_alive():
            if not messagebox.askyesno("Quit", "A download is in progress. Quit anyway?"):
                return
            self.stop_event.set()
        self.root.destroy()
