import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import matrics
from commands_step import StepsCommandsFrame


class CenterFrame(ttk.LabelFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, text="Программа", padding=10)
        self.controller = controller
        self.lift_offset = 10  # Величина поднятия по умолчанию (мм)

        # Инициализация переменных
        self.program_running = False
        self.program_paused = False
        self.current_step = tk.StringVar(value="0")
        self.current_coords = {
            "X": tk.StringVar(value="0.00"),
            "Y": tk.StringVar(value="0.00"),
            "Z": tk.StringVar(value="0.00")
        }
        self.lamp_states = {
            "Вакуум": tk.BooleanVar(value=False),
            "Доза": tk.BooleanVar(value=False),
            "Магазин": tk.BooleanVar(value=False)
        }

        # Загрузка позиций
        positions = matrics.get_positions()
        self.glue_point = {
            "X": tk.StringVar(value=positions['glue_point']['X']),
            "Y": tk.StringVar(value=positions['glue_point']['Y']),
            "Z": tk.StringVar(value=positions['glue_point']['Z']),
            "rows": tk.StringVar(value=positions['glue_point']['rows']),
            "cols": tk.StringVar(value=positions['glue_point']['cols'])
        }
        self.magazine_pos = {
            "X": tk.StringVar(value=positions['magazine_pos']['X']),
            "Y": tk.StringVar(value=positions['magazine_pos']['Y']),
            "Z": tk.StringVar(value=positions['magazine_pos']['Z'])
        }

        # Создание элементов интерфейса
        self.setup_ui()

        # Привязка событий
        for var in [*self.glue_point.values(), *self.magazine_pos.values()]:
            var.trace_add("write", self._update_positions)

    def validate_numeric_input(self, new_value):
        """Валидация числового ввода с поддержкой отрицательных значений"""
        if new_value == "" or new_value == "-":
            return True
        try:
            float(new_value)
            return True
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число (допустим знак минус)")
            return False

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Фрейм управления программой
        control_frame = ttk.LabelFrame(self, text="Управление", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Кнопки управления
        btn_style = {
            'width': 8,
            'height': 1,
            'font': ('Arial', 10, 'bold'),
            'bg': 'lightgray'
        }

        self.start_button = tk.Button(
            control_frame,
            text="Старт",
            command=self.start_program,
            **btn_style
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = tk.Button(
            control_frame,
            text="Пауза",
            command=self.pause_program,
            **btn_style
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.restart_button = tk.Button(
            control_frame,
            text="Повтор",
            command=self.restart_program,
            **btn_style
        )
        self.restart_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(
            control_frame,
            text="Стоп",
            command=self.stop_program,
            **btn_style
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)


        # Позиция клеевой точки
        glue_frame = ttk.LabelFrame(self, text="Позиция клеевой точки", padding=10)
        glue_frame.pack(fill=tk.X, padx=5, pady=5)

        coords_grid_frame = ttk.Frame(glue_frame)
        coords_grid_frame.pack(fill=tk.X, pady=2)

        for coord in ["X", "Y", "Z"]:
            ttk.Label(coords_grid_frame, text=f"{coord}:").pack(side=tk.LEFT, padx=2)
            entry = ttk.Entry(
                coords_grid_frame,
                textvariable=self.glue_point[coord],
                width=8,
                validate="key"
            )
            entry.configure(
                validatecommand=(self.register(self.validate_numeric_input), "%P")
            )
            entry.pack(side=tk.LEFT, padx=2)

        ttk.Separator(coords_grid_frame, orient='vertical').pack(side=tk.LEFT, padx=5, fill='y')

        ttk.Label(coords_grid_frame, text="Кол.строк:").pack(side=tk.LEFT, padx=2)
        rows_entry = ttk.Entry(
            coords_grid_frame,
            textvariable=self.glue_point['rows'],
            width=8,
            validate="key"
        )
        rows_entry.configure(
            validatecommand=(self.register(self.validate_numeric_input), "%P")
        )
        rows_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(coords_grid_frame, text="Кол.столбцов:").pack(side=tk.LEFT, padx=2)
        cols_entry = ttk.Entry(
            coords_grid_frame,
            textvariable=self.glue_point['cols'],
            width=8,
            validate="key"
        )
        cols_entry.configure(
            validatecommand=(self.register(self.validate_numeric_input), "%P")
        )
        cols_entry.pack(side=tk.LEFT, padx=2)

        # Позиция магазина
        magazine_frame = ttk.LabelFrame(self, text="Позиция магазина", padding=10)
        magazine_frame.pack(fill=tk.X, padx=5, pady=5)

        for i, coord in enumerate(["X", "Y", "Z"]):
            ttk.Label(magazine_frame, text=f"{coord}:").grid(row=0, column=i * 2, padx=5, pady=2)
            entry = ttk.Entry(
                magazine_frame,
                textvariable=self.magazine_pos[coord],
                width=10,
                validate="key"
            )
            entry.configure(
                validatecommand=(self.register(self.validate_numeric_input), "%P")
            )
            entry.grid(row=0, column=i * 2 + 1, padx=5, pady=2)

        # Текущее состояние
        status_frame = ttk.LabelFrame(self, text="Текущее состояние", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        status_row = ttk.Frame(status_frame)
        status_row.pack(fill=tk.X, pady=5)

        for coord in ["X", "Y", "Z"]:
            ttk.Label(status_row, text=f"{coord}:").pack(side=tk.LEFT, padx=2)
            ttk.Label(status_row, textvariable=self.current_coords[coord], width=6).pack(side=tk.LEFT)

        ttk.Label(status_row, text="Шаг:").pack(side=tk.LEFT, padx=2)
        ttk.Label(status_row, textvariable=self.current_step, width=6).pack(side=tk.LEFT)

        for lamp in self.lamp_states:
            row = ttk.Frame(status_row)
            row.pack(side=tk.LEFT, padx=5)
            indicator = ttk.Label(row, text="⬤", font=('Arial', 14), width=2)
            indicator.pack(side=tk.LEFT, padx=2)
            ttk.Label(row, text=lamp, width=8 if lamp in ["Вакуум", "Магазин"] else 6).pack(side=tk.LEFT)
            self.lamp_states[lamp].trace_add('write',
                                             lambda *_, l=lamp, i=indicator: self.update_lamp_indicator(l, i))

        # Кнопки сохранения/загрузки
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)

        ttk.Button(
            button_frame,
            text="Сохранить",
            command=self.save_steps,
            width=15
        ).pack(side=tk.LEFT, padx=5, expand=True)

        ttk.Button(
            button_frame,
            text="Загрузить",
            command=self.load_steps,
            width=15
        ).pack(side=tk.LEFT, padx=5, expand=True)

        # Фрейм с шагами и командами
        self.steps_commands = StepsCommandsFrame(self, self.controller)

    def lift_up(self):
        """Обработка команды поднятия"""
        try:
            current_z = float(self.current_coords["Z"].get())
            new_z = current_z + self.lift_offset

            # Обновляем текущие координаты
            self.current_coords["Z"].set(f"{new_z:.2f}")

            # Отправляем команду (через контроллер)
            self.controller.send_command(f"Подняться {self.lift_offset}")

            print(f"Поднятие выполнено. Z: {current_z:.2f} -> {new_z:.2f}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить поднятие: {str(e)}")

    def _update_positions(self, *args):
        """Обновляет позиции в matrics.py"""
        glue_data = {
            'X': self.glue_point['X'].get(),
            'Y': self.glue_point['Y'].get(),
            'Z': self.glue_point['Z'].get(),
            'rows': self.glue_point['rows'].get(),
            'cols': self.glue_point['cols'].get()
        }
        magazine_data = {k: v.get() for k, v in self.magazine_pos.items()}

        # Пропускаем сохранение если значение только "-"
        if any(v == "-" for v in [*glue_data.values(), *magazine_data.values()]):
            return

        try:
            matrics.save_positions(glue_data, magazine_data)
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректные данные: {str(e)}")

    def update_lamp_indicator(self, lamp, indicator):
        """Обновляет индикатор лампы"""
        state = self.lamp_states[lamp].get()
        color = "green" if state else "red"
        indicator.config(foreground=color)

    def start_program(self):
        """Запускает выполнение программы"""
        if not self.program_running:
            self.program_running = True
            self.program_paused = False
            print("Программа запущена")

    def pause_program(self):
        """Ставит программу на паузу"""
        if self.program_running and not self.program_paused:
            self.program_paused = True
            print("Программа на паузе")

    def restart_program(self):
        """Перезапускает программу"""
        if self.program_running:
            self.program_paused = False
            self.current_step.set("0")
            print("Программа перезапущена")

    def stop_program(self):
        """Останавливает выполнение программы"""
        if self.program_running:
            self.program_running = False
            self.program_paused = False
            self.current_step.set("0")
            print("Программа остановлена")

    def save_steps(self):
        """Сохраняет программу в файл JSON"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Сохранить программу"
        )
        if not filepath:
            return

        data = {
            "steps": self.steps_commands.get_steps(),
            "glue_point": {
                'X': self.glue_point['X'].get(),
                'Y': self.glue_point['Y'].get(),
                'Z': self.glue_point['Z'].get(),
                'rows': self.glue_point['rows'].get(),
                'cols': self.glue_point['cols'].get()
            },
            "magazine_pos": {k: v.get() for k, v in self.magazine_pos.items()}
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self._update_positions()
            print(f"Программа сохранена в {filepath}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")

    def load_steps(self):
        """Загружает программу из файла JSON"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            title="Загрузить программу"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Очищаем текущие шаги
            for step_num in list(self.steps_commands.steps.keys()):
                self.steps_commands.delete_step(self.steps_commands.step_frames[step_num])

            # Загружаем новые шаги
            for step_num, command in sorted(data["steps"].items()):
                self.steps_commands.add_command(command)

            # Загружаем позиции
            glue_data = data.get("glue_point", {})
            for k in ['X', 'Y', 'Z', 'rows', 'cols']:
                if k in glue_data:
                    self.glue_point[k].set(glue_data[k])

            for k in ["X", "Y", "Z"]:
                if k in data.get("magazine_pos", {}):
                    self.magazine_pos[k].set(data["magazine_pos"][k])

            self._update_positions()
            print(f"Программа загружена из {filepath}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке: {str(e)}")