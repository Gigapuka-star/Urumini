import os
import tempfile
import time
from tkinter import Canvas

import customtkinter as ctk

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    Image = None
    ImageDraw = None
    HAS_PIL = False


class MiniPaintWindow(ctk.CTkToplevel):
    def __init__(self, master_app):
        super().__init__(master_app)
        self.title("🎨 Швидкий малюнок")
        self.geometry("760x640")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.master_app = master_app

        if HAS_PIL:
            self.image = Image.new("RGB", (640, 520), "white")
            self.draw = ImageDraw.Draw(self.image)
        else:
            self.image = None
            self.draw = None

        self.canvas = Canvas(self, width=640, height=460, bg="white", cursor="cross")
        self.canvas.pack(fill="both", expand=True, padx=8, pady=(6, 4))

        self.pen_color = "black"
        self.pen_width = 10
        self.eraser_mode = False
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset_coords)
        self.last_x, self.last_y = None, None

        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(side="bottom", pady=6, fill="x", padx=8)

        BTN_W2, BTN_H2, BTN_CR2 = 40, 40, 18
        self.btn_clear = ctk.CTkButton(
            self.footer_frame,
            text="🗑️",
            fg_color="#A30000",
            hover_color="#D30000",
            width=BTN_W2,
            height=BTN_H2,
            corner_radius=BTN_CR2,
            command=self.clear_canvas,
        )
        self.btn_clear.pack(side="left", padx=(10, 8), pady=4)

        self.btn_eraser = ctk.CTkButton(
            self.footer_frame,
            text="🧼",
            fg_color="#555555",
            hover_color="#777777",
            width=BTN_W2,
            height=BTN_H2,
            corner_radius=BTN_CR2,
            command=self.toggle_eraser,
        )
        self.btn_eraser.pack(side="left", padx=(0, 8), pady=4)

        self.color_frame = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        self.color_frame.pack(side="left", padx=(0, 0), pady=4)
        colors = ["#000000", "#ff3860", "#00c853", "#1e88e5", "#f9a825"]
        for col in colors:
            btn = ctk.CTkButton(
                self.color_frame,
                text="",
                fg_color=col,
                hover_color=col,
                width=BTN_W2,
                height=BTN_H2,
                corner_radius=BTN_CR2,
                command=lambda c=col: self.set_pen_color(c),
            )
            btn.pack(side="left", padx=6)

        self.send_frame = ctk.CTkFrame(self.footer_frame, fg_color="transparent", width=110, height=BTN_H2 + 8)
        self.send_frame.pack(side="right", padx=(0, 10), pady=4)
        self.send_frame.pack_propagate(False)

        self.size_frame = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        self.size_frame.pack(side="left", padx=(10, 0), pady=4, fill="both", expand=True)
        self.brush_lbl = ctk.CTkLabel(self.size_frame, text=f"Розмір: {self.pen_width}", font=("Segoe UI", 12))
        self.brush_lbl.pack(side="left", padx=(6, 8))
        self.brush_slider = ctk.CTkSlider(self.size_frame, from_=1, to=50, number_of_steps=49, command=self._on_brush_size)
        self.brush_slider.set(self.pen_width)
        self.brush_slider.pack(side="left", fill="x", expand=True, padx=(4, 4))

        self.btn_send = ctk.CTkButton(
            self.send_frame,
            text="✅ Надіслати",
            fg_color="#1E6F3D",
            hover_color="#278A4D",
            width=100,
            height=BTN_H2,
            corner_radius=BTN_CR2,
            command=self.save_and_attach,
        )
        self.btn_send.pack(side="top", padx=0, pady=0, expand=True, fill="y")

    def paint(self, event):
        if self.last_x is not None and self.last_y is not None:
            draw_color = "white" if self.eraser_mode else self.pen_color
            self.canvas.create_line(
                self.last_x,
                self.last_y,
                event.x,
                event.y,
                width=self.pen_width,
                fill=draw_color,
                capstyle="round",
                smooth=True,
            )
            if self.draw:
                try:
                    self.draw.line([self.last_x, self.last_y, event.x, event.y], fill=draw_color, width=self.pen_width)
                except Exception:
                    pass
        self.last_x, self.last_y = event.x, event.y

    def reset_coords(self, event):
        self.last_x, self.last_y = None, None

    def clear_canvas(self):
        self.canvas.delete("all")
        self.eraser_mode = False
        self.btn_eraser.configure(fg_color="#555555")
        if HAS_PIL:
            self.image = Image.new("RGB", (640, 520), "white")
            self.draw = ImageDraw.Draw(self.image)
        else:
            self.image = None
            self.draw = None

    def save_and_attach(self):
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"gemini_draw_{int(time.time())}.png")
        if HAS_PIL and self.image:
            try:
                self.image.save(temp_path, "PNG")
            except Exception:
                open(temp_path, "wb").close()
        else:
            open(temp_path, "wb").close()
        self.master_app.attached_file_path = temp_path
        self.master_app.attachment_label.configure(text=f"🎨 {os.path.basename(temp_path)}")
        self.master_app.attachment_frame.pack(side="top", fill="x", before=self.master_app.controls_frame)
        self.destroy()

    def toggle_eraser(self):
        self.eraser_mode = not self.eraser_mode
        self.btn_eraser.configure(fg_color="#FFD700" if self.eraser_mode else "#555555")

    def _on_brush_size(self, value):
        self.pen_width = int(float(value))
        self.brush_lbl.configure(text=f"Розмір: {self.pen_width}")

    def set_pen_color(self, color):
        self.pen_color = color
        self.eraser_mode = False
        self.btn_eraser.configure(fg_color="#555555")
