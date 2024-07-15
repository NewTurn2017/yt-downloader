import tkinter as tk
from tkinter import filedialog, ttk
import yt_dlp
import threading
import os
import re
import subprocess


class YouTubeDownloaderGUI:
    def __init__(self, master):
        self.master = master
        master.title("YouTube 다운로더 by Genie")

        # URL 입력
        self.url_label = tk.Label(master, text="YouTube URL:")
        self.url_label.pack()
        self.url_entry = tk.Text(master, height=5, width=50)
        self.url_entry.pack()

        # 붙여넣기 이벤트 바인딩
        self.url_entry.bind('<Control-v>', self.paste)
        self.url_entry.bind('<Command-v>', self.paste)  # macOS용

        # 출력 폴더 선택
        self.folder_label = tk.Label(master, text="출력 폴더:")
        self.folder_label.pack()
        self.folder_entry = tk.Entry(master, width=50)
        self.folder_entry.pack()
        self.folder_button = tk.Button(
            master, text="폴더 선택", command=self.select_folder)
        self.folder_button.pack()

        # 출력 폴더 바로가기 버튼
        self.open_folder_button = tk.Button(
            master, text="출력 폴더 열기", command=self.open_output_folder)
        self.open_folder_button.pack()

        # 다운로드 버튼
        self.download_button = tk.Button(
            master, text="다운로드", command=self.start_download)
        self.download_button.pack()

        # 프로그레스 바 컨테이너
        self.progress_frame = tk.Frame(master)
        self.progress_frame.pack()

        # 프로그레스 바
        self.progress_bars = {}

        # 프로그레스 바와 파일 이름을 위한 프레임
        self.progress_frames = {}

    def paste(self, event):
        try:
            self.url_entry.insert(tk.INSERT, self.master.clipboard_get())
        except tk.TclError:
            pass
        return 'break'

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, folder_selected)

    def open_output_folder(self):
        folder_path = self.folder_entry.get()
        if folder_path:
            if os.path.exists(folder_path):
                if os.name == 'nt':  # Windows
                    os.startfile(folder_path)
                elif os.name == 'posix':  # macOS and Linux
                    subprocess.call(['open', folder_path])
            else:
                tk.messagebox.showerror("오류", "선택한 폴더가 존재하지 않습니다.")
        else:
            tk.messagebox.showerror("오류", "출력 폴더를 선택해주세요.")

    def start_download(self):
        urls = self.url_entry.get("1.0", tk.END).strip().split("\n")
        output_path = self.folder_entry.get()

        for url in urls:
            thread = threading.Thread(
                target=self.download_video, args=(url, output_path))
            thread.start()

    def download_video(self, url, output_path):
        progress_frame = tk.Frame(self.progress_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)

        filename_label = tk.Label(
            progress_frame, text="다운로드 준비 중...", anchor="w")
        filename_label.pack(fill=tk.X)

        progress_bar = ttk.Progressbar(
            progress_frame, length=300, mode='determinate')
        progress_bar.pack(fill=tk.X)

        self.progress_frames[url] = {
            "frame": progress_frame, "label": filename_label, "bar": progress_bar}

        def progress_hook(d):
            if d['status'] == 'downloading':
                filename = d.get('filename', '').split('/')[-1]
                truncated_filename = self.truncate_filename(filename, 40)
                p = d.get('_percent_str', '0%')
                p = re.sub(r'\x1b\[[0-9;]*m', '', p)
                p = float(p.replace('%', ''))
                self.master.after(0, lambda: self.update_progress(
                    url, truncated_filename, p))
            elif d['status'] == 'finished':
                self.master.after(0, lambda: self.remove_progress_bar(url))

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print(f"다운로드 중 오류 발생: {str(e)}")
            self.master.after(0, lambda: self.remove_progress_bar(url))

    def update_progress(self, url, filename, value):
        if url in self.progress_frames:
            self.progress_frames[url]["label"].config(text=filename)
            self.progress_frames[url]["bar"]['value'] = value

    def remove_progress_bar(self, url):
        if url in self.progress_frames:
            self.progress_frames[url]["frame"].destroy()
            del self.progress_frames[url]

    def truncate_filename(self, filename, max_length):
        if len(filename) <= max_length:
            return filename
        return filename[:max_length-3] + "..."


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()
