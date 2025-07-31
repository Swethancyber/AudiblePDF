import pyttsx3
import pdfplumber
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, Scale, HORIZONTAL
import threading

# Initialize TTS engine
engine = pyttsx3.init()
reading_thread = None  # To hold the reading thread
stop_event = threading.Event() # Event to signal stopping the reading

def set_voice_properties(rate, volume, voice_id=None):
    """Sets the speech rate, volume, and optionally the voice."""
    engine.setProperty('rate', rate)
    engine.setProperty('volume', volume / 100.0) # Convert percentage to 0.0-1.0
    if voice_id:
        engine.setProperty('voice', voice_id)

def get_available_voices():
    """Returns a list of available voices."""
    voices = engine.getProperty('voices')
    return [{"id": voice.id, "name": voice.name} for voice in voices]

def read_pdf_content(file_path, text_widget, progress_label, status_label):
    """Reads PDF content and speaks it aloud."""
    global reading_thread
    stop_event.clear() # Clear the stop event for a new reading session

    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                if stop_event.is_set():
                    # This check is crucial for stopping gracefully
                    engine.stop() # Immediately stop current speech
                    root.after(0, lambda: status_label.config(text="Reading Canceled."))
                    root.after(0, lambda: progress_label.config(text="Reading Progress: 0%"))
                    return # Exit the function
                
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                
                # Update progress
                progress = int(((i + 1) / total_pages) * 100)
                root.after(0, lambda p=progress: progress_label.config(text=f"Reading Progress: {p}%"))

        # If loop finishes without stop_event being set, then proceed to speak
        # Display text
        root.after(0, lambda: text_widget.delete(1.0, tk.END))
        root.after(0, lambda: text_widget.insert(tk.END, text))
        
        root.after(0, lambda: status_label.config(text="Reading aloud..."))
        engine.say(text)
        engine.runAndWait()
        
        # Check stop_event again after runAndWait, as it can be set while speaking
        if not stop_event.is_set(): 
            root.after(0, lambda: status_label.config(text="Reading Finished."))
        else:
            root.after(0, lambda: status_label.config(text="Reading Canceled.")) # In case it was cancelled during runAndWait

    except Exception as e:
        messagebox.showerror("Error", str(e))
        root.after(0, lambda: status_label.config(text="Error during reading."))
    finally:
        reading_thread = None # Reset the thread holder
        stop_event.clear() # Ensure event is cleared for next read


def browse_file(text_widget, progress_label, status_label):
    """Opens a file dialog to select a PDF and starts reading in a new thread."""
    global reading_thread
    if reading_thread and reading_thread.is_alive():
        messagebox.showwarning("Already Reading", "Please cancel the current reading before opening a new PDF.")
        return

    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        status_label.config(text="Loading PDF...")
        progress_label.config(text="Reading Progress: 0%")
        # Start reading in a new thread
        reading_thread = threading.Thread(target=read_pdf_content, args=(file_path, text_widget, progress_label, status_label), daemon=True)
        reading_thread.start()

def cancel_reading(status_label, progress_label):
    """Cancels the ongoing PDF reading."""
    global reading_thread
    if reading_thread and reading_thread.is_alive():
        stop_event.set() # Signal the thread to stop
        engine.stop()    # Immediately stop pyttsx3 speech
        status_label.config(text="Reading Stopped.")
        progress_label.config(text="Reading Progress: 0%")
    else:
        status_label.config(text="No reading in progress to stop.")
        # messagebox.showinfo("No Reading", "No PDF reading is currently in progress.") # Optional: remove this if status label is enough

def update_voice_settings(event=None):
    """Updates the voice properties based on slider values and selected voice."""
    rate = rate_slider.get()
    volume = volume_slider.get()
    
    selected_voice_name = voice_var.get()
    selected_voice_id = next((v["id"] for v in available_voices if v["name"] == selected_voice_name), None)
    
    set_voice_properties(rate, volume, selected_voice_id)

def on_closing():
    """Handles the window closing event, stopping speech and threads."""
    global reading_thread
    if reading_thread and reading_thread.is_alive():
        stop_event.set() # Signal the reading thread to stop
        engine.stop()    # Immediately stop pyttsx3 speech
        # Give the thread a moment to finish, but don't block the main thread indefinitely
        # reading_thread.join(timeout=1) # Optional: Wait a short time for the thread to join
    engine.stop() # Ensure engine is stopped even if no thread was active
    root.destroy() # Destroy the Tkinter window

# GUI Setup
root = tk.Tk()
root.title("🗣️ Enhanced PDF Reader")
root.geometry("900x650") # Slightly larger window

# Bind the on_closing function to the window's close protocol
root.protocol("WM_DELETE_WINDOW", on_closing)

# --- Top Frame for Controls ---
control_frame = tk.Frame(root, padx=10, pady=10)
control_frame.pack(fill=tk.X)

# Labels for better aesthetics
tk.Label(control_frame, text="Speech Settings:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))

# Voice Rate Slider
tk.Label(control_frame, text="Rate:").pack(side=tk.LEFT)
rate_slider = Scale(control_frame, from_=100, to=300, orient=HORIZONTAL, command=update_voice_settings)
rate_slider.set(engine.getProperty('rate')) # Set initial value
rate_slider.pack(side=tk.LEFT, padx=5)

# Volume Slider
tk.Label(control_frame, text="Volume:").pack(side=tk.LEFT)
volume_slider = Scale(control_frame, from_=0, to=100, orient=HORIZONTAL, command=update_voice_settings)
volume_slider.set(int(engine.getProperty('volume') * 100)) # Set initial value
volume_slider.pack(side=tk.LEFT, padx=5)

# Voice Selection
available_voices = get_available_voices()
voice_names = [v["name"] for v in available_voices]
voice_var = tk.StringVar(root)
if voice_names:
    voice_var.set(voice_names[0]) # Set initial voice
    voice_dropdown = tk.OptionMenu(control_frame, voice_var, *voice_names, command=update_voice_settings)
    voice_dropdown.pack(side=tk.LEFT, padx=5)
    tk.Label(control_frame, text="Voice:").pack(side=tk.LEFT)
else:
    tk.Label(control_frame, text="No voices found.", fg="red").pack(side=tk.LEFT, padx=5)

# --- Button Frame ---
button_frame = tk.Frame(root, pady=5)
button_frame.pack(fill=tk.X)

browse_button = tk.Button(button_frame, text="📂 Open PDF", command=lambda: browse_file(text_area, progress_label, status_label), font=("Arial", 10, "bold"), bg="#4CAF50", fg="white")
browse_button.pack(side=tk.LEFT, padx=10, pady=5)

# IMPORTANT CHANGE HERE: Pass progress_label to cancel_reading
cancel_button = tk.Button(button_frame, text="🚫 Cancel Reading", command=lambda: cancel_reading(status_label, progress_label), font=("Arial", 10, "bold"), bg="#FF5733", fg="white")
cancel_button.pack(side=tk.LEFT, padx=10, pady=5)

# --- Status and Progress Labels ---
status_label = tk.Label(root, text="Ready", font=("Arial", 10, "italic"), fg="blue")
status_label.pack(pady=5)

progress_label = tk.Label(root, text="Reading Progress: 0%", font=("Arial", 10, "italic"), fg="gray")
progress_label.pack(pady=2)

# --- Text Area for PDF Content ---
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Arial", 12), bg="#F8F8F8", relief=tk.FLAT, borderwidth=5)
text_area.pack(expand=True, fill="both", padx=10, pady=10)

# Initialize voice settings on startup
update_voice_settings()

root.mainloop()