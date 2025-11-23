import clr
import os
import json
import tkinter as tk
from tkinter import colorchooser
from tkinter import font
from screeninfo import get_monitors
import csv
from datetime import datetime

base_path = os.path.dirname(os.path.abspath(__file__))
dll_path = os.path.join(base_path, "OpenHardwareMonitorLib.dll")
clr.AddReference(dll_path)

from OpenHardwareMonitor import Hardware


class TempHUD:
    def __init__(self, CONFIG_FILE="config.json"):

        self.log_buffer = []
        self.log_limit = 1

        self.CONFIG_FILE = CONFIG_FILE
        self.config = self.load_config()

        # Cria janela principal
        self.root = tk.Tk()
        self.root.title("Temperaturas")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", self.config["color"]["alpha"])
        self.root.overrideredirect(True)
        self.root.configure(bg=self.config["color"]["background"])

        # Label
        self.label = tk.Label(
            self.root,
            text="Inicializando...",
            font=(
                self.config["font"]["family"],
                self.config["font"]["size"],
                self.config["font"]["weight"],
            ),
            bg=self.config["color"]["background"],
            fg=self.config["color"]["font"],
            justify="center",
            width=25,
        )
        self.label.pack(padx=8, pady=5)

        # Criar menu de contexto
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(
            label="Resetar registros", command=self.reset_max_min_values
        )
        self.menu.add_command(
            label="Alterar posição", command=self.open_position_window
        )
        self.menu.add_command(label="Alterar cor", command=self.open_color_window)
        self.menu.add_command(label="Alterar fonte", command=self.open_font_window)
        self.menu.add_command(
            label="Alterar temporizador", command=self.open_timer_window
        )

        # Exibir menu ao clicar com botão direito
        self.root.bind("<Button-3>", self.show_context_menu)

        # Bind para encerrar com o botão do meio
        self.root.bind("<Button-2>", lambda e: self.root.destroy())

        # Armazenamento das temperaturas máximas e mínimas
        self.max_values = {}
        self.min_values = {}

        self.computer = Hardware.Computer()
        self.computer.MainboardEnabled = True
        self.computer.CPUEnabled = True
        self.computer.GPUEnabled = True
        self.computer.Open()

        self.update_temps()

        # Posiciona a janela
        self.apply_position()

        self.root.mainloop()

    def load_config(self):
        DEFAULT_CONFIG = {
            "position": {
                "horizontal": "right",
                "vertical": "top",
                "margin_x": 10,
                "margin_y": 10,
            },
            "color": {"background": "#111", "alpha": 0.7, "font": "#FFF"},
            "font": {"family": "Consolas", "size": 8, "weight": "bold"},
            "timer": 5000,
        }

        if not os.path.exists(self.CONFIG_FILE):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG

        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except:
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG

    def registrar_leitura(self, cpu_temp, gpu_temp):
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_buffer.append(
            {"datetime": data_hora, "cpu": cpu_temp, "gpu": gpu_temp}
        )

        # Se atingiu 10 registros → salva no CSV
        if len(self.log_buffer) >= self.log_limit:
            self.salvar_csv()

    def salvar_csv(self):
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        filename = f"logs_{data_hoje}.csv"
        novo_arquivo = not os.path.exists(filename)

        try:
            with open(filename, "a", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, delimiter=";")

                # Cria cabeçalho se for arquivo novo
                if novo_arquivo:
                    header = ["timestamp", "cpu", "gpu"]
                    writer.writerow(header)

                # Escreve todas as linhas pendentes
                for row in self.log_buffer:
                    writer.writerow(
                        [
                            row.get("datetime", ""),
                            row.get("cpu", ""),
                            row.get("gpu", ""),
                        ]
                    )

            # Se chegou até aqui, salvou com sucesso → limpar buffer
            self.log_buffer.clear()

        except PermissionError:
            # Arquivo está aberto/bloqueado → não limpar buffer
            print(
                f"[AVISO] Arquivo '{filename}' está em uso. Tentando novamente depois."
            )

        except Exception as e:
            # Qualquer outro erro inesperado
            print(f"[ERRO] Falha ao salvar CSV: {e}")

    def save_config(self, data=None):
        if data == None:
            data = self.config

        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Erro ao salvar config:", e)

    def show_context_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def apply_position(self):
        self.root.update_idletasks()

        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        # Horizontal
        if self.config["position"]["horizontal"] == "right":
            x = sw - w - self.config["position"]["margin_x"]
        else:
            x = self.config["position"]["margin_x"]

        # Vertical
        if self.config["position"]["vertical"] == "top":
            y = self.config["position"]["margin_y"]
        else:
            y = sh - h - self.config["position"]["margin_y"]

        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def apply_colors(self):
        self.root.attributes("-alpha", self.config["color"]["alpha"])
        self.root.configure(bg=self.config["color"]["background"])
        self.label.config(bg=self.config["color"]["background"])
        self.label.config(fg=self.config["color"]["font"])

    def apply_font(self):
        self.label.config(
            font=(
                self.config["font"]["family"],
                self.config["font"]["size"],
                self.config["font"]["weight"],
            )
        )
        self.apply_position()

    def reset_max_min_values(self):
        self.max_values = {}
        self.min_values = {}
        self.update_temps()

    def open_position_window(self):
        win = tk.Toplevel(self.root)
        win.title("Alterar posição")
        win.geometry("260x400")
        win.resizable(False, True)

        # Horizontal
        tk.Label(win, text="Horizontal:").pack(pady=5)
        horiz_var = tk.StringVar(value=self.config["position"]["horizontal"])
        tk.Radiobutton(win, text="Direita", variable=horiz_var, value="right").pack()
        tk.Radiobutton(win, text="Esquerda", variable=horiz_var, value="left").pack()

        # Vertical
        tk.Label(win, text="Vertical:").pack(pady=5)
        vert_var = tk.StringVar(value=self.config["position"]["vertical"])
        tk.Radiobutton(win, text="Superior", variable=vert_var, value="top").pack()
        tk.Radiobutton(win, text="Inferior", variable=vert_var, value="bottom").pack()

        # Margem X
        tk.Label(win, text="Margem da borda horizontal (px):").pack(pady=5)
        margin_x_var = tk.StringVar(value=str(self.config["position"]["margin_x"]))
        margin_x_entry = tk.Entry(win, textvariable=margin_x_var)
        margin_x_entry.pack()

        # Margem Y
        tk.Label(win, text="Margem da borda vertical (px):").pack(pady=5)
        margin_y_var = tk.StringVar(value=str(self.config["position"]["margin_y"]))
        margin_y_entry = tk.Entry(win, textvariable=margin_y_var)
        margin_y_entry.pack()

        # Salvar
        def save():
            horiz = horiz_var.get().strip().lower()
            vert = vert_var.get().strip().lower()
            margin_x = int(margin_x_var.get().strip())
            margin_y = int(margin_y_var.get().strip())

            if horiz not in ("left", "right"):
                print("Valor horizontal inválido")
                return

            if vert not in ("top", "bottom"):
                print("Valor vertical inválido")
                return

            self.config["position"]["horizontal"] = horiz
            self.config["position"]["vertical"] = vert
            self.config["position"]["margin_x"] = margin_x
            self.config["position"]["margin_y"] = margin_y

            self.save_config()
            self.apply_position()
            win.destroy()

        tk.Button(win, text="Salvar", command=save).pack(pady=10)

    def open_color_window(self):
        win = tk.Toplevel(self.root)
        win.title("Alterar cor")
        win.geometry("310x230")
        win.resizable(False, False)

        # Valores atuais
        bg_color_var = tk.StringVar(value=self.config["color"]["background"])
        fg_color_var = tk.StringVar(value=self.config["color"]["font"])

        # --- Cor de fundo ---
        tk.Label(win, text="Cor do fundo:").pack(anchor="w", padx=10, pady=(10, 0))

        def escolher_cor_fundo():
            cor = colorchooser.askcolor(initialcolor=bg_color_var.get())
            if cor[1]:
                bg_color_var.set(cor[1])

        tk.Button(win, text="Selecionar cor do fundo", command=escolher_cor_fundo).pack(
            anchor="w", padx=10
        )

        # --- Cor do texto ---
        tk.Label(win, text="Cor do texto:").pack(anchor="w", padx=10, pady=(10, 0))

        def escolher_cor_texto():
            cor = colorchooser.askcolor(initialcolor=fg_color_var.get())
            if cor[1]:
                fg_color_var.set(cor[1])

        tk.Button(win, text="Selecionar cor do texto", command=escolher_cor_texto).pack(
            anchor="w", padx=10
        )

        # --- Opacidade ---
        tk.Label(win, text="Opacidade da janela:").pack(
            anchor="w", padx=10, pady=(10, 0)
        )
        # tk.Entry(win, textvariable=opacity_var, width=10).pack(anchor="w", padx=10)
        opacity_scale = tk.Scale(
            win, from_=0, to=100, orient=tk.HORIZONTAL, resolution=1
        )
        opacity_scale.set(self.config["color"]["alpha"] * 100)
        opacity_scale.pack()

        # Botão salvar
        def salvar():
            bg = bg_color_var.get()
            fg = fg_color_var.get()
            try:
                op = float(opacity_scale.get()) / 100
            except:
                op = self.config["color"]["alpha"]

            op = max(0.1, min(1.0, op))

            self.config["color"] = {
                "background": bg,
                "alpha": op,  # opacidade
                "font": fg,  # cor da fonte
            }

            self.save_config()
            self.apply_colors()
            win.destroy()

        tk.Button(win, text="Salvar", command=salvar).pack(pady=15)

    def open_font_window(self):
        win = tk.Toplevel(self.root)
        win.title("Alterar fonte")
        win.geometry("300x250")
        win.resizable(False, False)

        # ===== FONTES DISPONÍVEIS =====
        fonts = list(font.families())
        fonts.sort()

        # ===== VARIABLES =====
        font_family_var = tk.StringVar(value=self.config["font"]["family"])
        font_size_var = tk.StringVar(value=str(self.config["font"]["size"]))
        font_bold_var = tk.BooleanVar(value=(self.config["font"]["weight"] == "bold"))

        # ===== INTERFACE =====
        tk.Label(win, text="Fonte:").pack(anchor="w", padx=10, pady=(10, 0))
        family_select = tk.OptionMenu(win, font_family_var, *fonts)
        family_select.pack(anchor="w", padx=10)

        tk.Label(win, text="Tamanho:").pack(anchor="w", padx=10, pady=(10, 0))
        tk.Entry(win, textvariable=font_size_var, width=10).pack(anchor="w", padx=10)

        tk.Checkbutton(win, text="Negrito", variable=font_bold_var).pack(
            anchor="w", padx=10, pady=10
        )

        # ===== SAVE BUTTON =====
        def salvar():
            try:
                size = int(font_size_var.get())
            except:
                size = self.config["font"]["size"]

            weight = "bold" if font_bold_var.get() else "normal"

            self.config["font"] = {
                "family": font_family_var.get(),
                "size": size,
                "weight": weight,
            }

            self.save_config()
            self.apply_font()
            win.destroy()

        tk.Button(win, text="Salvar", command=salvar).pack(pady=15)

    def open_timer_window(self):
        win = tk.Toplevel(self.root)
        win.title("Alterar timer")
        win.geometry("260x150")
        win.resizable(False, False)

        tk.Label(win, text="Intervalo de atualização (ms):").pack(
            anchor="w", padx=10, pady=(10, 0)
        )

        timer_var = tk.StringVar(value=str(self.config["timer"]))
        tk.Entry(win, textvariable=timer_var, width=12).pack(anchor="w", padx=10)

        def salvar():
            try:
                novo_timer = int(timer_var.get())
                if novo_timer < 50:
                    novo_timer = 50  # mínimo para prevenir travamentos
            except:
                novo_timer = self.config["timer"]

            self.config["timer"] = novo_timer
            self.save_config()
            win.destroy()

        tk.Button(win, text="Salvar", command=salvar).pack(pady=15)

    def get_temps(self):
        data = {}
        for hw in self.computer.Hardware:
            hw.Update()
            for sensor in hw.Sensors:
                if sensor.SensorType == Hardware.SensorType.Temperature:
                    data[sensor.Name] = round(sensor.Value, 1)
        return data

    def update_temps(self):
        temps = self.get_temps()
        lines = []

        for name, value in temps.items():
            displayName = name[:3]
            if name not in self.max_values:
                self.max_values[name] = value
                self.min_values[name] = value
            else:
                self.max_values[name] = max(self.max_values[name], value)
                self.min_values[name] = min(self.min_values[name], value)
            lines.append(
                f"{displayName:3s}: {value:.1f}°C | {self.min_values[name]:.1f}~{self.max_values[name]:.1f}°C"
            )

            cpu_temp = None
            gpu_temp = None
            if f"{displayName:3s}" == "CPU":
                cpu_temp = f"{value:.1f}"
            else:
                gpu_temp = f"{value:.1f}"

        if not lines:
            lines = ["Nenhum sensor disponível"]

        self.registrar_leitura(cpu_temp, gpu_temp)

        self.label.config(text="\n".join(lines))
        self.root.after(self.config["timer"], self.update_temps)


if __name__ == "__main__":
    TempHUD()
