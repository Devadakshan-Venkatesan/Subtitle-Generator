import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os
import tempfile
import threading
from moviepy.editor import VideoFileClip
import assemblyai as aai

class SubtitleMakerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Subtitle Maker")
        self.minsize(450, 250)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.winfo_reqwidth()) // 2
        y = (screen_height - self.winfo_reqheight()) // 2
        self.geometry("+{}+{}".format(x, y))

        self.api_key_var = tk.StringVar()
        self.video_path_var = tk.StringVar()
        self.subtitle_folder_var = tk.StringVar()
        self.subtitle_name_var = tk.StringVar()

        self.api_key_frame = ctk.CTkFrame(self)
        self.file_selection_frame = ctk.CTkFrame(self)

        self.create_api_key_frame()
        self.create_file_selection_frame()
        self.show_frame(self.api_key_frame)

    def create_api_key_frame(self):
        ctk.CTkLabel(self.api_key_frame, text="Enter AssemblyAI API Key : ").grid(row=0, column=0, padx=(10, 0), pady=(10, 5), sticky="w")
        ctk.CTkEntry(self.api_key_frame, textvariable=self.api_key_var, width=150, show="*").grid(row=0, column=1, padx=(0, 10), pady=(10, 5), sticky="ew")
        ctk.CTkButton(self.api_key_frame, text="Next", command=self.show_file_selection_frame).grid(row=1, columnspan=2, pady=20)

    def create_file_selection_frame(self):
        ctk.CTkLabel(self.file_selection_frame, text="Video File : ").grid(row=0, column=0, padx=(10, 0), pady=(10, 5), sticky="w")
        ctk.CTkEntry(self.file_selection_frame, textvariable=self.video_path_var, width=150).grid(row=0, column=1, padx=(0, 10), pady=(10, 5), sticky="ew")
        ctk.CTkButton(self.file_selection_frame, text="Browse", command=self.select_video_file).grid(row=0, column=2, padx=(0, 10), pady=(10, 5), sticky="ew")

        ctk.CTkLabel(self.file_selection_frame, text="Save Subtitle To : ").grid(row=1, column=0, padx=(10, 0), pady=(10, 5), sticky="w")
        ctk.CTkEntry(self.file_selection_frame, textvariable=self.subtitle_folder_var, width=150).grid(row=1, column=1, padx=(0, 10), pady=(10, 5), sticky="ew")
        ctk.CTkButton(self.file_selection_frame, text="Browse", command=self.select_subtitle_folder).grid(row=1, column=2, padx=(0, 10), pady=(10, 5), sticky="ew")

        ctk.CTkLabel(self.file_selection_frame, text="Subtitle File Name : ").grid(row=2, column=0, padx=(10, 0), pady=(10, 5), sticky="w")
        ctk.CTkEntry(self.file_selection_frame, textvariable=self.subtitle_name_var, width=150).grid(row=2, column=1, padx=(0, 10), pady=(10, 5), sticky="ew")

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(self.file_selection_frame, variable=self.progress_var, width=200)
        self.progress_bar.grid(row=3, columnspan=3, padx=(10, 10), pady=(10, 5), sticky="ew")
        self.progress_bar.grid_remove()

        self.progress_bar_label = ctk.CTkLabel(self.file_selection_frame, text="")
        self.progress_bar_label.grid(row=4, column=0, columnspan=3, pady=10, sticky="ew")

        self.convert_button = ctk.CTkButton(self.file_selection_frame, text="Convert to Subtitles", command=self.convert_video_to_subtitles, width=10)
        self.convert_button.grid(row=5, columnspan=3, padx=(10, 10), pady=(10, 5), sticky="ew")

    def show_frame(self, frame):
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def show_file_selection_frame(self):
        if not self.api_key_var.get():
            messagebox.showerror("Error", "Please enter your AssemblyAI API key")
        else:
            self.show_frame(self.file_selection_frame)

    def select_video_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.avi;*.mkv")])
        self.video_path_var.set(file_path)

    def select_subtitle_folder(self):
        folder_path = filedialog.askdirectory()
        self.subtitle_folder_var.set(folder_path)

    def convert_video_to_subtitles(self):
        video_path = self.video_path_var.get()
        api_key = self.api_key_var.get()
        subtitle_folder = self.subtitle_folder_var.get()
        subtitle_name = self.subtitle_name_var.get()

        if not video_path or not subtitle_folder or not subtitle_name:
            messagebox.showerror("Error", "Please fill all fields")
            return

        self.convert_button.configure(state="disabled")
        self.disable_ui()
        threading.Thread(target=self.process_video, args=(video_path, api_key, subtitle_folder, subtitle_name)).start()

    def process_video(self, video_path, api_key, subtitle_folder, subtitle_name):
        try:
            self.update_progress(0.1, "Extracting audio from video...")
            with tempfile.TemporaryDirectory() as tmp_dir:
                audio_path = os.path.join(tmp_dir, os.path.splitext(os.path.basename(video_path))[0] + ".mp3")
                subtitles_path = os.path.join(subtitle_folder, subtitle_name + ".srt")

                video = VideoFileClip(video_path)
                audio = video.audio
                audio.write_audiofile(audio_path)

                self.update_progress(0.5, "Transcribing audio to text...")
                aai.settings.api_key = api_key
                transcript = aai.Transcriber().transcribe(audio_path, aai.TranscriptionConfig(language_code="en"))
                subtitles = transcript.export_subtitles_srt()

                self.update_progress(0.9, "Saving subtitles to file...")
                with open(subtitles_path, "w") as f:
                    f.write(subtitles)

                os.remove(audio_path)
                self.update_progress(1.0, "Completed")
                self.show_message("Success", f"Subtitles saved to {subtitles_path}")
        except Exception as e:
            self.show_message("Error", str(e))
        finally:
            self.enable_ui()

    def update_progress(self, value, message):
        self.progress_var.set(value)
        self.progress_bar_label.configure(text=message)
        self.update_idletasks()

    def disable_ui(self):
        self.progress_bar.grid()
        self.progress_bar_label.configure(text="Starting process...")
        self.progress_var.set(0)
        self.progress_bar.update()
        self.update_idletasks()

    def enable_ui(self):
        self.convert_button.configure(state="normal")
        self.progress_bar.grid_remove()
        self.progress_bar_label.configure(text="")

    def show_message(self, title, message):
        messagebox.showinfo(title, message)

if __name__ == "__main__":
    app = SubtitleMakerApp()
    app.mainloop()
