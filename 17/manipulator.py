import matrics
import kinematics
import time
from steps_for_arduino import ArduinoStepSender
from serial_settings import SerialManager


class ManipulatorController:
    """
    Главный контроллер для управления манипулятором.
    Теперь использует единый SerialManager для всех операций с COM-портом.
    """

    def __init__(self, port=None):
        """
        Инициализация контроллера манипулятора.
        Args:
            port (str, optional): COM-порт для подключения. Defaults to None.
        """
        # Инициализация менеджера подключений
        self.serial_manager = SerialManager()

        # Настройка отправителя команд
        self.arduino_sender = ArduinoStepSender(debug_mode=False)

        # Текущее положение манипулятора (в мм)
        self.current_position = {'x': 0, 'y': 0, 'z': 1000}  # Z=1000 - верхнее положение
        self.grid_position = {'row': 0, 'col': 0}
        self.last_kinematics = {'x': 0, 'y': 0, 'z': 1000}

        # Модуль для расчетов кинематики
        self.kinematics = kinematics.Kinematics()

        # Параметры манипулятора
        self.lift_offset = 20  # Высота подъема над точкой (мм)
        self.was_rubbing = False  # Флаг выполнения притирки

    def execute_command(self, command):
        """
        Выполняет указанную команду манипулятора.
        Теперь использует JSON-формат для команд, совместимый с новым Arduino-скриптом.
        """
        cmd_map = {
            # Основные движения
            "В исходное положение": self.go_home,
            "Движение к печке": self.move_to_glue_point,
            "Движение к магазину": self.move_to_magazine,

            # Управление инструментами (новый JSON-формат)
            "Вперёд дозатором": lambda: self.arduino_sender.send_command({
                "command": "motor",
                "motor": 3,  # Пример для мотора дозатора
                "direction": 1,
                "steps": 500
            }),
            "Вперёд присоской": lambda: self.arduino_sender.send_command({
                "command": "motor",
                "motor": 2,  # Пример для мотора присоски
                "direction": 1,
                "steps": 600
            }),
            "Включить вакуум": lambda: self.arduino_sender.send_command({
                "command": "pneumatic",
                "valve1": True,
                "valve2": True
            }),
            "Выключить вакуум": lambda: self.arduino_sender.send_command({
                "command": "pneumatic",
                "valve1": False,
                "valve2": False
            }),
            "Включить дозатор": lambda: self.arduino_sender.send_command({
                "command": "pneumatic",
                "valve1": False,
                "valve2": True
            }),
            "Выключить дозатор": lambda: self.arduino_sender.send_command({
                "command": "pneumatic",
                "valve1": False,
                "valve2": False
            }),
            "Включить магазин": lambda: self.arduino_sender.send_command({
                "command": "servo",
                "state": True,
                "angle": 90
            }),

            # Управление высотой
            "Подняться": self.lift_up,
            "Опуститься до магазина": self.move_down_to_magazine,
            "Опуститься до печки": self.move_down_to_glue_point,

            # Специальные операции
            "Притирка": self.rubbing,

            # HOME-команда для калибровки
            "Калибровка": lambda: self.arduino_sender.send_command({
                "command": "HOME"
            })
        }

        if command in cmd_map:
            if not self.serial_manager.is_connected:
                print("Ошибка: Нет подключения к Arduino!")
                return

            try:
                cmd_map[command]()
                print(f"Команда '{command}' выполнена")
            except Exception as e:
                print(f"Ошибка выполнения команды '{command}': {str(e)}")
        else:
            print(f"Ошибка: Неизвестная команда '{command}'")

    def go_home(self):
        """Возвращает манипулятор в исходное положение (Z=1000)."""
        lift_diff = self.kinematics.calculate_lift(self.kinematics.MAX_Z)

        self.arduino_sender.send_step(
            ruka=-1000,
            plecho=-1000,
            lift=lift_diff,
            orgon=-1000
        )

        self._reset_positions()

    def move_to_glue_point(self):
        """Перемещает манипулятор к текущей точке на печке."""
        grid = matrics.get_grid_coordinates()
        current_pos = (self.grid_position['row'], self.grid_position['col'])

        if current_pos not in grid:
            print(f"Ошибка: Позиция {current_pos} отсутствует в сетке")
            return

        coords = grid[current_pos]
        target_x, target_y = float(coords['X']), float(coords['Y'])
        current_z = self.current_position['z']

        if self.was_rubbing:
            self._move_directly_after_rubbing(target_x, target_y, current_z)
            self.was_rubbing = False
        else:
            self._move_to(target_x, target_y, current_z)

        print(f"Перемещение к точке печки: X={target_x:.1f}, Y={target_y:.1f}")

    def _move_directly_after_rubbing(self, x, y, z):
        """Прямое перемещение после притирки без промежуточных шагов."""
        current_x, current_y = self.current_position['x'], self.current_position['y']
        self._update_grid_position()

        new_pos = (self.grid_position['row'], self.grid_position['col'])
        grid = matrics.get_grid_coordinates()

        if new_pos in grid:
            new_coords = grid[new_pos]
            new_x, new_y = float(new_coords['X']), float(new_coords['Y'])

            self.kinematics.set_positions(
                x=current_x, y=current_y, z=z,
                x1=new_x, y1=new_y, z1=z
            )
            shoulder_diff, arm_diff, _ = self.kinematics.calculate_difference()

            self.arduino_sender.send_step(ruka=arm_diff, plecho=shoulder_diff)
            self._update_positions(new_x, new_y, z)

            print(f"Смещение к новой позиции: X={new_x:.1f}, Y={new_y:.1f}")

    def move_to_magazine(self):
        """Перемещает манипулятор к позиции магазина."""
        magazine = matrics.magazine_pos
        target_x, target_y = float(magazine['X']), float(magazine['Y'])
        current_z = self.current_position['z']

        self._move_to(target_x, target_y, current_z)
        print(f"Перемещение к магазину: X={target_x:.1f}, Y={target_y:.1f}")

    def lift_up(self):
        """Поднимает манипулятор на заданное расстояние над текущей позицией."""
        try:
            glue_z = float(matrics.glue_point['Z'])
            current_z = self.current_position['z']
            target_z = min(glue_z + self.lift_offset, self.kinematics.MAX_Z)

            self.kinematics.set_positions(z=current_z, z1=target_z)
            _, _, lift_diff = self.kinematics.calculate_difference()

            self.arduino_sender.send_step(lift=lift_diff)
            self.current_position['z'] = target_z
            self.last_kinematics['z'] = target_z

            print(f"Поднятие на {self.lift_offset}мм: Z={current_z:.1f} -> {target_z:.1f}")
        except Exception as e:
            print(f"Ошибка при поднятии: {str(e)}")

    def rubbing(self):
        """Выполняет операцию притирки (6 циклов движения)."""
        self.arduino_sender.start_rubbing()
        print(f'Шаг {self.arduino_sender.step_counter}: PRITIRKA')

        for i, value in enumerate([100.00, -100.00, 100.00, -100.00, 100.00, -100.00], 1):
            self.arduino_sender.send_rubbing_step(i, value)
            print(f'Шаг {self.arduino_sender.step_counter}.{i}: RUKA={value:.2f}')
            time.sleep(0.5)

        self.arduino_sender.end_rubbing()
        self.was_rubbing = True
        print("Притирка выполнена. Следующее перемещение обновит позицию.")

    def move_down_to_magazine(self):
        """Опускает манипулятор до уровня магазина."""
        target_z = float(matrics.magazine_pos['Z'])
        self._move_down(target_z)
        print(f"Опускание до магазина: Z={target_z:.1f}")

    def move_down_to_glue_point(self):
        """Опускает манипулятор до уровня печки."""
        target_z = float(matrics.glue_point['Z'])
        self._move_down(target_z)
        print(f"Опускание до печки: Z={target_z:.1f}")

    def _move_down(self, target_z):
        """Внутренний метод для опускания манипулятора."""
        current_z = self.current_position['z']
        self.kinematics.set_positions(z=current_z, z1=target_z)
        _, _, lift_diff = self.kinematics.calculate_difference()

        self.arduino_sender.send_step(lift=lift_diff)
        self.last_kinematics['z'] = target_z
        self.current_position['z'] = target_z

    def _move_to(self, x, y, z):
        """
        Внутренний метод перемещения в указанные координаты XY.
        Args:
            x (float): Целевая координата X
            y (float): Целевая координата Y
            z (float): Текущая координата Z (высота)
        """
        self.kinematics.set_positions(
            x=self.last_kinematics['x'],
            y=self.last_kinematics['y'],
            z=z,
            x1=x,
            y1=y,
            z1=z
        )

        shoulder_diff, arm_diff, _ = self.kinematics.calculate_difference()
        self.arduino_sender.send_step(ruka=arm_diff, plecho=shoulder_diff)
        self._update_positions(x, y, z)

    def _update_positions(self, x, y, z):
        """
        Обновляет текущие позиции манипулятора.
        Args:
            x (float): Новая координата X
            y (float): Новая координата Y
            z (float): Новая координата Z
        """
        self.last_kinematics = {'x': x, 'y': y, 'z': z}
        self.current_position = {'x': x, 'y': y, 'z': z}

    def _update_grid_position(self):
        """Обновляет позицию в рабочей сетке (автоматический инкремент)."""
        rows = int(matrics.glue_point['rows'])
        cols = int(matrics.glue_point['cols'])

        old_row, old_col = self.grid_position['row'], self.grid_position['col']

        if self.grid_position['col'] < cols - 1:
            self.grid_position['col'] += 1
        else:
            self.grid_position['col'] = 0
            if self.grid_position['row'] < rows - 1:
                self.grid_position['row'] += 1
            else:
                self.grid_position['row'] = 0

        if (old_row, old_col) != (self.grid_position['row'], self.grid_position['col']):
            print(f"Новая позиция в сетке: строка={self.grid_position['row']}, столбец={self.grid_position['col']}")

    def _reset_positions(self):
        """Полный сброс всех позиций в начальное состояние."""
        self.current_position = {'x': 0.0, 'y': 0.0, 'z': self.kinematics.MAX_Z}
        self.grid_position = {'row': 0, 'col': 0}
        self.last_kinematics = {'x': 0.0, 'y': 0.0, 'z': self.kinematics.MAX_Z}
        self.kinematics.reset_positions()
        self.was_rubbing = False