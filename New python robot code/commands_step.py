import tkinter as tk
from tkinter import ttk


class StepsCommandsFrame:
    """
    Класс для создания интерфейса управления шагами программы манипулятора.
    Состоит из двух частей:
    - Список текущих шагов программы (с возможностью редактирования и удаления)
    - Панель с доступными командами для добавления в программу
    """

    def __init__(self, parent, controller):
        """
        Инициализация фрейма
        :param parent: родительский виджет
        :param controller: контроллер для отправки команд
        """
        self.controller = controller
        self.steps = {}  # Словарь для хранения шагов {номер: виджет Entry}
        self.step_frames = {}  # Словарь для хранения фреймов шагов
        self.current_step_num = 0  # Текущий номер шага

        # Создаем основной контейнер
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Инициализируем обе части интерфейса
        self.setup_steps_frame()  # Левая часть - список шагов
        self.setup_commands_frame()  # Правая часть - доступные команды

    def setup_steps_frame(self):
        """Создает фрейм со списком шагов программы с возможностью прокрутки"""
        # Создаем контейнер для списка шагов
        steps_frame = ttk.LabelFrame(self.main_frame, text="Команды по шагам", padding=10, width=280)
        steps_frame.pack_propagate(False)  # Фиксируем ширину
        steps_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)

        # Настройка прокрутки
        self.canvas = tk.Canvas(steps_frame, width=240)
        scrollbar = ttk.Scrollbar(steps_frame, orient="vertical", command=self.canvas.yview)

        # Фрейм для содержимого с прокруткой
        self.scrollable_frame = ttk.Frame(self.canvas, width=240)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Размещаем элементы
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Настройка прокрутки колесиком мыши
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.scrollable_frame.bind("<MouseWheel>",
                                   lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Размещаем canvas и scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Добавляем первый шаг по умолчанию
        self.add_command("В исходное положение")

    def setup_commands_frame(self):
        """Создает фрейм с кнопками доступных команд"""
        commands_frame = ttk.LabelFrame(self.main_frame, text="Команды", padding=10)
        commands_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        # Список всех доступных команд
        commands = [
            "В исходное положение", "Движение к печке", "Движение к магазину",
            "Вперёд дозатором", "Вперёд присоской", "Включить вакуум",
            "Выключить вакуум", "Включить дозатор", "Выключить дозатор",
            "Включить магазин", "Подняться", "Опуститься до магазина",
            "Опуститься до печки", "Притирка"
        ]

        # Создаем кнопки команд (по 2 в ряд)
        for i in range(0, len(commands), 2):
            row = ttk.Frame(commands_frame)
            row.pack(fill=tk.X, pady=2)

            # Добавляем две кнопки в текущий ряд
            for j in range(2):
                if i + j < len(commands):
                    ttk.Button(
                        row,
                        text=commands[i + j],
                        command=lambda c=commands[i + j]: self.add_command(c),
                        width=22
                    ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

    def add_command(self, command):
        """
        Добавляет новую команду в список шагов
        :param command: текст команды для добавления
        """
        self.current_step_num += 1

        # Создаем фрейм для шага
        step_frame = ttk.Frame(self.scrollable_frame)
        step_frame.pack(fill=tk.X, pady=2)

        # Добавляем метку с номером шага
        ttk.Label(step_frame, text=f"Шаг {self.current_step_num}:", width=8).pack(side=tk.LEFT)

        # Поле для редактирования команды
        entry = ttk.Entry(step_frame, width=25)
        entry.insert(0, command)  # Вставляем переданную команду
        entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # Кнопка удаления шага
        ttk.Button(
            step_frame,
            text="×",  # Знак умножения как иконка удаления
            width=2,
            command=lambda f=step_frame: self.delete_step(f)
        ).pack(side=tk.RIGHT)

        # Сохраняем ссылки на элементы
        self.steps[self.current_step_num] = entry
        self.step_frames[self.current_step_num] = step_frame

    def delete_step(self, step_frame):
        """
        Удаляет указанный шаг из программы
        :param step_frame: фрейм шага для удаления
        """
        # Находим и удаляем шаг
        for step_num, frame in list(self.step_frames.items()):
            if frame == step_frame:
                del self.steps[step_num]
                del self.step_frames[step_num]
                step_frame.destroy()
                self.renumber_steps()  # Перенумеровываем оставшиеся шаги
                break

    def renumber_steps(self):
        """Перенумеровывает шаги после удаления"""
        # Сортируем оставшиеся шаги по номеру
        sorted_frames = sorted(self.step_frames.items(), key=lambda x: x[0])

        # Очищаем текущие данные
        self.steps.clear()
        self.step_frames.clear()
        self.current_step_num = 0

        # Перенумеровываем шаги
        for old_num, frame in sorted_frames:
            for child in frame.winfo_children():
                if isinstance(child, ttk.Entry):
                    self.current_step_num += 1
                    # Обновляем номер шага в метке
                    frame.winfo_children()[0].config(text=f"Шаг {self.current_step_num}:")
                    # Сохраняем с новым номером
                    self.steps[self.current_step_num] = child
                    self.step_frames[self.current_step_num] = frame
                    break

    def get_steps(self):
        """
        Возвращает список всех шагов программы
        :return: словарь {номер_шага: команда}
        """
        return {step: self.steps[step].get() for step in sorted(self.steps)}