import json
import os
import queue
import sys
import threading
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageOps

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".nullbit.json")

LANGUAGES = {
    "RU": {
        "title": "NullBit - Очистка",
        "btn_select": "Выбрать фото и очистить",
        "ask_open": "Выберите фотографии",
        "ask_save_dir": "Выберите папку для сохранения",
        "status_ready": "Жду файлы...",
        "status_processing": "Обработка файлов...",
        "status_progress": "Обработка: {} / {}",
        "status_success": "Успешно очищено: {} фото\nСохранено в выбранную папку",
        "status_partial": "Очищено: {}, не удалось: {}",
        "status_error": "Ошибка: {}",
        "author": "Автор: vadhorvad "
    },
    "EN": {
        "title": "NullBit - Cleaner",
        "btn_select": "Select Photos & Clean",
        "ask_open": "Select Photos",
        "ask_save_dir": "Select folder to save",
        "status_ready": "Waiting for files...",
        "status_processing": "Processing...",
        "status_progress": "Processing: {} / {}",
        "status_success": "Successfully cleaned: {} photos\nSaved to selected folder",
        "status_partial": "Cleaned: {}, failed: {}",
        "status_error": "Error: {}",
        "author": "Author: vadhorvad "
    },
    "SR": {
        "title": "NullBit - Čistač",
        "btn_select": "Izaberi slike i očisti",
        "ask_open": "Izaberite slike",
        "ask_save_dir": "Izaberite folder za čuvanje",
        "status_ready": "Čekam fajlove...",
        "status_processing": "Obrada...",
        "status_progress": "Obrada: {} / {}",
        "status_success": "Uspešno očišćeno: {} slika\nSačuvano u izabrani folder",
        "status_partial": "Očišćeno: {}, neuspešno: {}",
        "status_error": "Greška: {}",
        "author": "Autor: vadhorvad "
    }
}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_language():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            lang = json.load(f).get("language")
    except Exception:
        return "RU"
    return lang if lang in LANGUAGES else "RU"

def save_language(lang):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"language": lang}, f)
    except Exception:
        pass

def unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"

def to_saveable_mode(image):
    if image.mode == "CMYK":
        return image.convert("RGB")
    image = image.convert("RGBA") if image.mode in ("P", "PA", "LA") else image
    if "A" in image.getbands():
        flat = Image.new("RGB", image.size, (255, 255, 255))
        flat.paste(image, mask=image.getchannel("A"))
        return flat
    return image.convert("RGB")

def save_clean(image, filepath):
    try:
        image.save(filepath, quality=100, subsampling=0)
    except OSError:
        # Some pixel modes (CMYK, 16-bit, palette+alpha) can't be stored in
        # every format — fall back to a broadly supported mode instead of failing.
        save_clean(to_saveable_mode(image), filepath)

def clean_file(filepath, save_dir):
    """Rebuild the pixel map on a blank canvas so no metadata survives.

    Returns the path of the saved copy.
    """
    with Image.open(filepath) as img:
        # Bake the EXIF rotation into the pixels before the EXIF block is destroyed,
        # otherwise portrait photos come out sideways.
        img = ImageOps.exif_transpose(img)
        clean_image = Image.new(img.mode, img.size)
        clean_image.paste(img)

        name, ext = os.path.splitext(os.path.basename(filepath))
        target = unique_path(os.path.join(save_dir, f"{name}_nullbit{ext}"))
        save_clean(clean_image, target)
    return target

class NullBitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.current_lang = load_language()
        self.texts = LANGUAGES[self.current_lang]

        self.title("NullBit")
        self.geometry("450x520")
        self.resizable(False, False)

        self.configure(fg_color="#F4F6F9")

        self.icon_path = resource_path("favicon.ico")

        def set_icon():
            try:
                if os.path.exists(self.icon_path):
                    self.wm_iconbitmap(self.icon_path)
            except Exception:
                pass

        self.after(200, set_icon)

        self.job_queue = queue.Queue()
        self.after(100, self.poll_queue)

        self.grid_columnconfigure(0, weight=1)

        self.lang_selector = ctk.CTkSegmentedButton(
            self,
            values=["RU", "EN", "SR"],
            command=self.change_language,
            font=("Roboto", 12, "bold")
        )
        self.lang_selector.set(self.current_lang)
        self.lang_selector.grid(row=0, column=0, pady=(20, 10), padx=20)

        self.logo_label = ctk.CTkLabel(self, text="")
        self.load_logo()
        self.logo_label.grid(row=1, column=0, pady=(10, 30))

        self.btn_select = ctk.CTkButton(
            self,
            text=self.texts["btn_select"],
            command=self.process_images,
            width=250,
            height=50,
            font=("Roboto", 15, "bold"),
            corner_radius=10,
            fg_color="#12243A",
            hover_color="#1C385A"
        )
        self.btn_select.grid(row=2, column=0, pady=10)

        self.status_label = ctk.CTkLabel(
            self,
            text=self.texts["status_ready"],
            font=("Roboto", 14),
            text_color="#555555",
            wraplength=400
        )
        self.status_label.grid(row=3, column=0, pady=20)

        self.author_label = ctk.CTkLabel(
            self,
            text=self.texts["author"],
            font=("Roboto", 12),
            text_color="#7F8C8D"
        )
        self.author_label.grid(row=4, column=0, pady=(20, 20), sticky="s")

    def load_logo(self):
        logo_path = resource_path("logo.jpg")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(180, 180))
                self.logo_label.configure(image=ctk_img)
            except Exception:
                pass

    def change_language(self, new_lang):
        self.current_lang = new_lang
        self.texts = LANGUAGES[self.current_lang]

        self.title(self.texts["title"])
        self.btn_select.configure(text=self.texts["btn_select"])
        self.status_label.configure(text=self.texts["status_ready"])
        self.author_label.configure(text=self.texts["author"])
        save_language(new_lang)

    def process_images(self):
        filepaths = filedialog.askopenfilenames(
            title=self.texts["ask_open"],
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.tiff")]
        )

        if not filepaths:
            return

        save_dir = filedialog.askdirectory(
            title=self.texts["ask_save_dir"]
        )

        if not save_dir:
            return

        self.btn_select.configure(state="disabled")
        self.status_label.configure(
            text=self.texts["status_processing"],
            text_color="#2980B9"
        )
        threading.Thread(
            target=self.process_worker,
            args=(tuple(filepaths), save_dir),
            daemon=True
        ).start()

    def process_worker(self, filepaths, save_dir):
        total = len(filepaths)
        cleaned = 0
        failed = 0
        last_error = None

        for index, filepath in enumerate(filepaths, 1):
            try:
                clean_file(filepath, save_dir)
                cleaned += 1
            except Exception as e:
                failed += 1
                last_error = e
            self.job_queue.put(("progress", index, total))

        self.job_queue.put(("done", cleaned, failed, last_error))

    def poll_queue(self):
        try:
            while True:
                message = self.job_queue.get_nowait()
                if message[0] == "progress":
                    _, index, total = message
                    self.status_label.configure(
                        text=self.texts["status_progress"].format(index, total)
                    )
                else:
                    _, cleaned, failed, last_error = message
                    self.show_result(cleaned, failed, last_error)
        except queue.Empty:
            pass
        self.after(100, self.poll_queue)

    def show_result(self, cleaned, failed, last_error):
        self.btn_select.configure(state="normal")
        if failed and not cleaned:
            self.status_label.configure(
                text=self.texts["status_error"].format(str(last_error)),
                text_color="#C0392B"
            )
        elif failed:
            self.status_label.configure(
                text=self.texts["status_partial"].format(cleaned, failed),
                text_color="#E67E22"
            )
        else:
            self.status_label.configure(
                text=self.texts["status_success"].format(cleaned),
                text_color="#27AE60"
            )

if __name__ == "__main__":
    app = NullBitApp()
    app.mainloop()
