import os
import sys
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

LANGUAGES = {
    "RU": {
        "title": "NullBit - Очистка",
        "btn_select": "Выбрать фото и очистить",
        "ask_save_dir": "Выберите папку для сохранения",
        "status_ready": "Жду файлы...",
        "status_processing": "Обработка файлов...",
        "status_success": "Успешно очищено: {} фото\nСохранено в выбранную папку",
        "status_error": "Ошибка: {}",
        "author": "Автор: vadhorvad "
    },
    "EN": {
        "title": "NullBit - Cleaner",
        "btn_select": "Select Photos & Clean",
        "ask_save_dir": "Select folder to save",
        "status_ready": "Waiting for files...",
        "status_processing": "Processing...",
        "status_success": "Successfully cleaned: {} photos\nSaved to selected folder",
        "status_error": "Error: {}",
        "author": "Author: vadhorvad "
    },
    "SR": {
        "title": "NullBit - Čistač",
        "btn_select": "Izaberi slike i očisti",
        "ask_save_dir": "Izaberite folder za čuvanje",
        "status_ready": "Čekam fajlove...",
        "status_processing": "Obrada...",
        "status_success": "Uspešno očišćeno: {} slika\nSačuvano u izabrani folder",
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

class NullBitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.current_lang = "RU"
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

    def process_images(self):
        filepaths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.tiff")]
        )
        
        if not filepaths:
            return

        save_dir = filedialog.askdirectory(
            title=self.texts["ask_save_dir"]
        )
        
        if not save_dir:
            return

        self.status_label.configure(
            text=self.texts["status_processing"],
            text_color="#2980B9"
        )
        self.update() 

        success_count = 0

        try:
            for filepath in filepaths:
                img = Image.open(filepath)
                
                clean_image = Image.new(img.mode, img.size)
                clean_image.paste(img)
                
                _, filename = os.path.split(filepath)
                name, ext = os.path.splitext(filename)
                new_filename = f"{name}_nullbit{ext}"
                new_filepath = os.path.join(save_dir, new_filename)
                
                clean_image.save(new_filepath, quality=100)
                success_count += 1
            
            self.status_label.configure(
                text=self.texts["status_success"].format(success_count),
                text_color="#27AE60"
            )
            
        except Exception as e:
            self.status_label.configure(
                text=self.texts["status_error"].format(str(e)),
                text_color="#C0392B"
            )

if __name__ == "__main__":
    app = NullBitApp()
    app.mainloop()