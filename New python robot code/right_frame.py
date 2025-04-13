import tkinter as tk
from tkinter import ttk


class RightFrame(ttk.LabelFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, text="Ручное управление", width=400)
        self.controller = controller

        # Инициализация состояний
        self.motor_values = {f"Двигатель {part}": tk.DoubleVar(value=0.0)
                             for part in ["верхний", "нижний", "руки", "кисти"]}
        self.sliders = {}
        self.pneumatic_states = {"Присоска": False, "Дозатор": False}

        self.setup_motor_sliders()
        self.setup_pneumatic_controls()

    def setup_motor_sliders(self):
        for motor in self.motor_values:
            frame = ttk.Frame(self)
            frame.pack(fill=tk.X, padx=10, pady=8)
            ttk.Label(frame, text=motor, width=18, anchor="w").pack(side=tk.LEFT)
            ttk.Label(frame, text="-20", width=4).pack(side=tk.LEFT)
            slider = ttk.Scale(frame, from_=-20, to=20, variable=self.motor_values[motor],
                               command=lambda v, m=motor: self.on_slider_change(m, v))
            slider.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            slider.bind("<ButtonRelease-1>", lambda e, m=motor: self.on_slider_release(m))
            ttk.Label(frame, text="20", width=4).pack(side=tk.LEFT)
            value_frame = ttk.Frame(frame, width=50)
            value_frame.pack(side=tk.LEFT)
            ttk.Label(value_frame, text="=").pack(side=tk.LEFT)
            value_label = ttk.Label(value_frame, text="0.0", width=5)
            value_label.pack(side=tk.LEFT)
            self.motor_values[motor].label = value_label
            self.sliders[motor] = slider

    def setup_pneumatic_controls(self):
        frame = ttk.LabelFrame(self, text="Пневматика", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=10, ipady=5)

        for device in ["Присоска", "Дозатор"]:
            btn = tk.Button(frame, text=f"{device} ВКЛ", command=lambda d=device: self.toggle_pneumatic(d),
                            bg='lightgray', activebackground='lightgray', height=2,
                            font=('Arial', 10, 'bold'),
                            relief=tk.SUNKEN if self.pneumatic_states[device] else tk.RAISED)
            btn.pack(fill=tk.X, pady=5)
            setattr(self, f"{device.lower()}_button", btn)

    def on_slider_change(self, motor, value):
        self.motor_values[motor].label.config(text=f"{float(value):.1f}")
        self.controller.send_command(f"{motor[:3].upper()}:{float(value):.1f}")

    def on_slider_release(self, motor):
        current_value = self.motor_values[motor].get()
        if -1 <= current_value <= 1 and current_value != 0:
            self.motor_values[motor].set(0.0)
            self.sliders[motor].set(0.0)
            self.motor_values[motor].label.config(text="0.0")
            self.controller.send_command(f"{motor[:3].upper()}:0.0")

    def toggle_pneumatic(self, device):
        self.pneumatic_states[device] = not self.pneumatic_states[device]
        button = getattr(self, f"{device.lower()}_button")

        if self.pneumatic_states[device]:
            button.config(text=f"{device} ВЫКЛ", bg='lightblue', relief=tk.SUNKEN)
        else:
            button.config(text=f"{device} ВКЛ", bg='lightgray', relief=tk.RAISED)

        self.controller.send_command(f"{device[:3].upper()}:{int(self.pneumatic_states[device])}")