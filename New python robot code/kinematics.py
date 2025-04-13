import math


class Kinematics:
    """
    Класс для расчета кинематики манипулятора.
    Вычисляет углы поворота рычагов на основе координат.
    """

    def __init__(self):
        # Инициализация длин рычагов (в мм)
        self.L1 = 228  # Длина первого рычага (плечо)
        self.L2 = 147.123  # Длина второго рычага (предплечье)
        self.MAX_Z = 1000  # Максимальная высота (исходное положение)

        # Сброс всех позиций в начальное состояние
        self.reset_positions()

    def reset_positions(self):
        """
        Сбрасывает все позиции в начальное состояние.
        По умолчанию манипулятор поднят вверх (Z = MAX_Z).
        """
        self.x = self.y = 0.0  # Текущие координаты X, Y
        self.z = self.MAX_Z  # Текущая координата Z
        self.x1 = self.y1 = self.z1 = 0.0  # Целевые координаты

    def set_positions(self, x=None, y=None, z=None, x1=None, y1=None, z1=None):
        """
        Устанавливает текущие и целевые позиции.
        Автоматически ограничивает высоту значением MAX_Z.
        """
        if x is not None: self.x = x
        if y is not None: self.y = y
        if z is not None: self.z = min(float(z), self.MAX_Z)
        if x1 is not None: self.x1 = x1
        if y1 is not None: self.y1 = y1
        if z1 is not None: self.z1 = min(float(z1), self.MAX_Z)

    def calculate_difference(self):
        """
        Вычисляет разницу между текущей и целевой позицией.
        Возвращает кортеж: (разница_плечо, разница_рука, разница_Z)
        """
        # Вычисляем углы для текущей позиции
        current_arm, current_shoulder = self._calc_angles(self.x, self.y)

        # Вычисляем углы для целевой позиции
        target_arm, target_shoulder = self._calc_angles(self.x1, self.y1)

        # Разница по высоте (Z-координата)
        dz = self.z - self.z1

        return (target_shoulder - current_shoulder,
                target_arm - current_arm,
                dz)

    def calculate_lift(self, target_z):
        """
        Вычисляет разницу высот для подъема/опускания.
        Возвращает разницу между текущей и целевой высотой.
        """
        return self.z - target_z

    def _calc_angles(self, x, y):
        """
        Внутренний метод для вычисления углов поворота рычагов.
        Возвращает кортеж: (угол_руки, угол_плеча)
        """
        # Если координаты нулевые - возвращаем нулевые углы
        if x == 0 and y == 0:
            return 0.0, 0.0

        # Вычисляем расстояние до точки
        distance = math.hypot(x, y)

        # Вычисляем угол руки (по теореме косинусов)
        cos_arm = (self.L1 ** 2 + self.L2 ** 2 - distance ** 2) / (2 * self.L1 * self.L2)
        cos_arm = max(-1, min(1, cos_arm))  # Ограничиваем значение косинуса
        arm_angle = math.degrees(math.acos(cos_arm)) - 21  # Коррекция угла

        # Вычисляем угол плеча
        cos_beta = (distance ** 2 + self.L1 ** 2 - self.L2 ** 2) / (2 * distance * self.L1) if distance != 0 else 0
        cos_beta = max(-1, min(1, cos_beta))
        beta = math.degrees(math.acos(cos_beta)) if distance != 0 else 0

        # Учитываем квадрант, в котором находится точка
        direction = math.degrees(math.atan2(y, x))

        if x >= 0:
            if y >= 0:
                # Первый квадрант (x>0, y>0)
                shoulder_angle = beta + direction + 90
            else:
                # Четвертый квадрант (x>0, y<0)
                shoulder_angle = beta + math.degrees(math.atan2(x, -y))
        else:
            # Для отрицательных X корректируем углы
            arm_angle = 339 - math.degrees(math.acos(cos_arm))
            if y >= 0:
                # Второй квадрант (x<0, y>0)
                shoulder_angle = 180 + math.degrees(math.atan2(-x, y)) - beta
            else:
                # Третий квадрант (x<0, y<0)
                shoulder_angle = 270 + math.degrees(math.atan2(-y, -x)) - beta

        return arm_angle, shoulder_angle