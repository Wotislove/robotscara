import matrics
import kinematics
from steps_for_arduino import ArduinoStepSender


class ManipulatorController:
    """
    Главный контроллер для управления манипулятором.
    Обрабатывает команды, управляет перемещениями и взаимодействует с Arduino.
    """

    def __init__(self, port=None):
        """
        Инициализация контроллера манипулятора.

        Args:
            port (str, optional): COM-порт для подключения к Arduino. Defaults to None.
        """
        # Настройка соединения с Arduino (в режиме отладки)
        self.arduino_sender = ArduinoStepSender(port=port, debug_mode=True)

        # Текущее положение манипулятора (в мм)
        self.current_position = {'x': 0, 'y': 0, 'z': 1000}  # Z=1000 - верхнее положение

        # Положение в рабочей сетке (строка и столбец)
        self.grid_position = {'row': 0, 'col': 0}

        # Последние рассчитанные координаты для кинематики
        self.last_kinematics = {'x': 0, 'y': 0, 'z': 1000}

        # Модуль для расчетов кинематики
        self.kinematics = kinematics.Kinematics()

        # Параметры манипулятора
        self.lift_offset = 20  # Высота подъема над точкой (мм)
        self.was_rubbing = False  # Флаг выполнения притирки

    def execute_command(self, command):
        """
        Выполняет указанную команду манипулятора.

        Args:
            command (str): Название команды из списка доступных
        """
        # Словарь соответствия команд методам
        cmd_map = {
            # Основные движения
            "В исходное положение": self.go_home,
            "Движение к печке": self.move_to_glue_point,
            "Движение к магазину": self.move_to_magazine,

            # Управление инструментами
            "Вперёд дозатором": lambda: self.arduino_sender.send_step(orgon=500),
            "Вперёд присоской": lambda: self.arduino_sender.send_step(orgon=-600),
            "Включить вакуум": lambda: self.arduino_sender.send_step(vacuum="HIGH"),
            "Выключить вакуум": lambda: self.arduino_sender.send_step(vacuum="LOW"),
            "Включить дозатор": lambda: self.arduino_sender.send_step(doza="HIGH"),
            "Выключить дозатор": lambda: self.arduino_sender.send_step(doza="LOW"),
            "Включить магазин": lambda: self.arduino_sender.send_step(magazin=10),

            # Управление высотой
            "Подняться": self.lift_up,
            "Опуститься до магазина": self.move_down_to_magazine,
            "Опуститься до печки": self.move_down_to_glue_point,

            # Специальные операции
            "Притирка": self.rubbing
        }

        # Выполняем команду если она есть в словаре
        if command in cmd_map:
            cmd_map[command]()
        else:
            print(f"Ошибка: Неизвестная команда '{command}'")

    def go_home(self):
        """Возвращает манипулятор в исходное положение (Z=1000)."""
        # Рассчитываем подъем на максимальную высоту
        lift_diff = self.kinematics.calculate_lift(self.kinematics.MAX_Z)

        # Отправляем команды сброса на Arduino
        self.arduino_sender.send_step(
            ruka=-1000,  # Сброс положения руки
            plecho=-1000,  # Сброс положения плеча
            lift=lift_diff,  # Подъем на максимальную высоту
            orgon=-1000  # Сброс положения инструмента
        )

        # Сбрасываем все позиции и состояния
        self._reset_positions()
        print("Манипулятор возвращен в исходное положение")

    def move_to_glue_point(self):
        """Перемещает манипулятор к текущей точке на печке."""
        # Получаем координаты сетки из модуля matrics
        grid = matrics.get_grid_coordinates()
        current_pos = (self.grid_position['row'], self.grid_position['col'])

        # Проверяем что позиция существует в сетке
        if current_pos not in grid:
            print(f"Ошибка: Позиция {current_pos} отсутствует в сетке")
            return

        # Получаем координаты цели
        coords = grid[current_pos]
        target_x, target_y = float(coords['X']), float(coords['Y'])
        current_z = self.current_position['z']

        # Выполняем перемещение в XY-плоскости
        self._move_to(target_x, target_y, current_z)
        print(f"Перемещение к точке печки: X={target_x:.1f}, Y={target_y:.1f}")

        # Если была выполнена притирка, обновляем позицию
        if self.was_rubbing:
            self._update_position_after_rubbing(grid)

    def _update_position_after_rubbing(self, grid):
        """Обновляет позицию в сетке после выполнения притирки."""
        old_pos = (self.grid_position['row'], self.grid_position['col'])
        self._update_grid_position()
        new_pos = (self.grid_position['row'], self.grid_position['col'])

        # Если позиция изменилась, перемещаемся к новой точке
        if old_pos != new_pos and new_pos in grid:
            new_coords = grid[new_pos]
            new_x, new_y = float(new_coords['X']), float(new_coords['Y'])
            self._move_to(new_x, new_y, self.current_position['z'])
            print(f"Смещение к новой позиции: X={new_x:.1f}, Y={new_y:.1f}")

        self.was_rubbing = False

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

            # Устанавливаем новые позиции для расчета
            self.kinematics.set_positions(z=current_z, z1=target_z)

            # Рассчитываем и отправляем команду подъема
            _, _, lift_diff = self.kinematics.calculate_difference()
            self.arduino_sender.send_step(lift=lift_diff)

            # Обновляем текущие позиции
            self.current_position['z'] = target_z
            self.last_kinematics['z'] = target_z

            print(f"Поднятие на {self.lift_offset}мм: Z={current_z:.1f} -> {target_z:.1f}")

        except Exception as e:
            print(f"Ошибка при поднятии: {str(e)}")

    def rubbing(self):
        """Выполняет операцию притирки (3 цикла движения)."""
        for _ in range(3):
            self.arduino_sender.send_step(ruka=100)  # Движение вперед
            self.arduino_sender.send_step(ruka=-100)  # Движение назад

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

        # Устанавливаем позиции для расчета
        self.kinematics.set_positions(z=current_z, z1=target_z)

        # Рассчитываем и отправляем команду опускания
        _, _, lift_diff = self.kinematics.calculate_difference()
        self.arduino_sender.send_step(lift=lift_diff)

        # Обновляем текущие позиции
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
        # Устанавливаем текущие и целевые позиции
        self.kinematics.set_positions(
            x=self.last_kinematics['x'],
            y=self.last_kinematics['y'],
            z=z,
            x1=x,
            y1=y,
            z1=z
        )

        # Рассчитываем разницу положений
        shoulder_diff, arm_diff, _ = self.kinematics.calculate_difference()

        # Отправляем команды на Arduino
        self.arduino_sender.send_step(ruka=arm_diff, plecho=shoulder_diff)

        # Обновляем текущие позиции
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

        # Увеличиваем номер столбца
        if self.grid_position['col'] < cols - 1:
            self.grid_position['col'] += 1
        else:
            # Если достигли конца строки, переходим на новую строку
            self.grid_position['col'] = 0
            if self.grid_position['row'] < rows - 1:
                self.grid_position['row'] += 1
            else:
                # Если достигли конца сетки, начинаем сначала
                self.grid_position['row'] = 0

        print(f"Новая позиция в сетке: строка={self.grid_position['row']}, столбец={self.grid_position['col']}")

    def _reset_positions(self):
        """Полный сброс всех позиций в начальное состояние."""
        self.current_position = {'x': 0.0, 'y': 0.0, 'z': self.kinematics.MAX_Z}
        self.grid_position = {'row': 0, 'col': 0}
        self.last_kinematics = {'x': 0.0, 'y': 0.0, 'z': self.kinematics.MAX_Z}
        self.kinematics.reset_positions()
        self.was_rubbing = False