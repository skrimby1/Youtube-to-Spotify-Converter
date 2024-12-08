import os
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from tkinter import ttk
from yt_dlp import YoutubeDL
from PIL import Image, ImageTk
import requests
from io import BytesIO
from pydub import AudioSegment
import json  # For saving and loading user preferences

# Paths
config_file = "C:/Users/vikto/Documents/YouToSpo/config.json"  # Updated path
input_folder = ""  # Empty initially, will be set by user selection
output_folder = ""  # Empty initially, will be set by user selection
last_platform = "Select Platform"  # Default value for platform

# Ensure the directory for the config file exists
os.makedirs(os.path.dirname(config_file), exist_ok=True)

# Save configuration to a JSON file
def save_config(config):
    with open(config_file, "w") as file:
        json.dump(config, file)

# Load configuration from a JSON file
def load_config():
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            return json.load(file)
    return {}

# Update progress bar callback
def download_progress_hook(d):
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes', 1)
        percentage = (downloaded / total) * 100 if total > 0 else 0
        progress_var.set(percentage)
        progress_bar.update_idletasks()

# Download audio from YouTube or SoundCloud
def download_audio(url, platform, output_dir=input_folder):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'progress_hooks': [download_progress_hook],
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        thumbnail_url = info.get('thumbnail', None)
        return os.path.join(output_dir, f"{info['title']}.mp3"), thumbnail_url

# Convert MP3 to WAV
def mp3_to_wav(input_mp3, output_wav):
    audio = AudioSegment.from_mp3(input_mp3)
    audio = audio.set_frame_rate(44100)
    audio.export(output_wav, format="wav")
    return output_wav

# Convert folder of MP3 to WAV
def convert_folder_mp3_to_wav(input_folder=input_folder, output_folder=output_folder):
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".mp3"):
            input_mp3 = os.path.join(input_folder, filename)
            output_wav = os.path.join(output_folder, filename[:-4] + ".wav")
            
            # Convert MP3 to WAV
            try:
                mp3_to_wav(input_mp3, output_wav)
                print(f"Converted: {input_mp3} to {output_wav}")

                # Prompt the user to rename the file after conversion
                new_name = simpledialog.askstring("Rename File", f"Do you want to rename the file '{output_wav}'? Enter a new name, or leave empty to keep the current name.")
                
                if new_name:
                    # If the user entered a new name, rename the file
                    new_wav_path = os.path.join(output_folder, f"{new_name}.wav")
                    os.rename(output_wav, new_wav_path)
                    messagebox.showinfo("File Renamed", f"The file was renamed to: {new_wav_path}")
                else:
                    messagebox.showinfo("No Rename", "The file was not renamed.")
                
                # Delete the MP3 file after conversion
                os.remove(input_mp3)
                print(f"Deleted: {input_mp3}")
            except Exception as e:
                print(f"Error converting {input_mp3}: {e}")


# Fetch and display thumbnail
def fetch_thumbnail(thumbnail_url):
    if not thumbnail_url:
        messagebox.showwarning("Thumbnail Error", "No thumbnail URL available.")
        return None

    try:
        response = requests.get(thumbnail_url)
        img_data = BytesIO(response.content)

        img = Image.open(img_data)
        img.thumbnail((200, 200))

        thumbnail_image = ImageTk.PhotoImage(img)
        return thumbnail_image
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while fetching the thumbnail: {e}")
        return None

# GUI Functions
def download_audio_gui():
    url = url_entry.get()
    platform = platform_var.get()

    if not url:
        messagebox.showerror("Input Error", "Please enter a URL")
        return

    if platform == "Select Platform":
        messagebox.showerror("Input Error", "Please select a platform (YouTube or SoundCloud)")
        return

    try:
        # Reset the progress bar
        progress_var.set(0)
        progress_bar.update_idletasks()

        # Save the selected platform to the configuration
        save_config({"last_platform": platform, "input_folder": input_folder, "output_folder": output_folder})

        # Download audio and retrieve the thumbnail URL
        mp3_file, thumbnail_url = download_audio(url, platform, input_folder)
        messagebox.showinfo("Success", f"Downloaded: {mp3_file}")

        # Use the fetched thumbnail URL to display the thumbnail
        thumbnail_image = fetch_thumbnail(thumbnail_url)
        if thumbnail_image:
            thumbnail_label.config(image=thumbnail_image)
            thumbnail_label.image = thumbnail_image
    except Exception as e:
        messagebox.showerror("Download Error", f"An error occurred: {e}")

def convert_mp3_to_wav_gui():
    if not input_folder or not output_folder:
        messagebox.showerror("Directory Error", "Please select both input and output directories.")
        return

    try:
        convert_folder_mp3_to_wav(input_folder, output_folder)
        messagebox.showinfo("Success", "MP3 to WAV conversion complete")
    except Exception as e:
        messagebox.showerror("Conversion Error", f"An error occurred: {e}")

# Select directories for MP3 input and WAV output
def select_input_directory():
    global input_folder
    input_folder = filedialog.askdirectory(title="Select MP3 Conversion Directory")
    input_dir_label.config(text=f"Input Directory: {input_folder}")
    save_config({"input_folder": input_folder, "output_folder": output_folder, "last_platform": platform_var.get()})  # Save directory and platform

def select_output_directory():
    global output_folder
    output_folder = filedialog.askdirectory(title="Select Output Directory for WAV files")
    output_dir_label.config(text=f"Output Directory: {output_folder}")
    save_config({"input_folder": input_folder, "output_folder": output_folder, "last_platform": platform_var.get()})  # Save directory and platform

# Platform selection change handler to save the platform choice
def on_platform_change(event):
    platform = platform_var.get()
    save_config({"last_platform": platform, "input_folder": input_folder, "output_folder": output_folder})

# GUI Setup
root = tk.Tk()
root.title("Youtube to Spotify Converter")
try:
    root.iconbitmap("C:/Users/vikto/Documents/YouToSpo/restti.ico")
except Exception as e:
    print(f"Error setting icon: {e}")

# Load the configuration on start
config = load_config()
input_folder = config.get("input_folder", "")
output_folder = config.get("output_folder", "")
last_platform = config.get("last_platform", "Select Platform")

# URL Entry
url_label = tk.Label(root, text="Enter URL:")
url_label.pack(pady=5)
url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=5)

# Platform Selection
platform_label = tk.Label(root, text="Select Platform:")
platform_label.pack(pady=5)

platform_var = tk.StringVar(value=last_platform)
platform_combobox = ttk.Combobox(root, textvariable=platform_var, values=["Youtube", "SoundCloud"])
platform_combobox.pack(pady=5)
platform_combobox.bind("<<ComboboxSelected>>", on_platform_change)  # Save platform on change

# Directory Selection
input_dir_button = tk.Button(root, text="Select MP3 Input Directory", command=select_input_directory)
input_dir_button.pack(pady=5)

output_dir_button = tk.Button(root, text="Select Output Directory for WAV", command=select_output_directory)
output_dir_button.pack(pady=5)

input_dir_label = tk.Label(root, text=f"Input Directory: {input_folder if input_folder else 'Not Selected'}")
input_dir_label.pack(pady=5)

output_dir_label = tk.Label(root, text=f"Output Directory: {output_folder if output_folder else 'Not Selected'}")
output_dir_label.pack(pady=5)

# Buttons
download_button = tk.Button(root, text="Download to MP3", command=download_audio_gui)
download_button.pack(pady=10)

convert_button = tk.Button(root, text="Convert MP3 to WAV", command=convert_mp3_to_wav_gui)
convert_button.pack(pady=10)

# Progress Bar
progress_var = tk.DoubleVar()

progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=400)
progress_bar.pack(pady=10)
progress_bar.pack(padx=20)

# Thumbnail Display
thumbnail_label = tk.Label(root)
thumbnail_label.pack(pady=10)

# Start GUI
root.mainloop()
