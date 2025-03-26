import tkinter as tk
import serial
arduino = serial.Serial('COM3', 9600, timeout=10)
logic_value1 = False
logic_value = False
root =tk.Tk()
root.title ("Move")
def toggle_logic():
    global logic_value
    if logic_value == False:
        logic_value = True
        print("Впрыск воздуха ")
        arduino.write(b"N")
    else:
        logic_value = False
        print("Создание вакума")
        arduino.write(b"M")
def toggle_logic2():
    global logic_value1
    if logic_value1 == False:
        logic_value1 = True
        print("Впрыск клея")
        arduino.write(b"K")
    else:
        logic_value1 = False
        print("Отключение впрыска клея ")
        arduino.write(b"L")
def get_input():
    text1 = entry1.get()
    text2 = entry2.get()
    output_label.config(text=f"X: {text1} Y: {text2}")
def move_forward():
    arduino.write(b"F")
def move_reverse():
    arduino.write(b"R")
def move_to_home():
    arduino.write(b"H")
def stop_motor():
    arduino.write(b"S")
def move_arm_forward():
    arduino.write(b"X")
def move_arm_reverse():
    arduino.write(b"Z")
def move_elevator_forward():
    arduino.write(b"U")
def move_elevator_reverse():
    arduino.write(b"D")
def move_wrist_forward():
    arduino.write(b"V")
def move_wrist_reverse():
    arduino.write(b"B")

btn_forward =tk.Button(root, text="move",command=move_forward)
btn_forward.grid(row=0,column=0, ipadx=6,ipady=6,padx=5,pady=5)


btn_reverse =tk.Button(root, text="rev",command=move_reverse)
btn_reverse.grid(row=0,column=1, ipadx=6,ipady=6,padx=5,pady=5)

btn_home =tk.Button(root, text="home",command=move_to_home)
btn_home.grid(row=1,column=0, ipadx=6,ipady=6,padx=5,pady=5)

btn_stop =tk.Button(root, text="stop",command=stop_motor)
btn_stop.grid(row=1,column=1, ipadx=6,ipady=6,padx=5,pady=5)

btn_arm_forward =tk.Button(root, text="Arm move",command=move_arm_forward)
btn_arm_forward.grid(row=2,column=0, ipadx=6,ipady=6,padx=5,pady=5)

btn_arm_reverse =tk.Button(root, text="Arm rev",command=move_arm_reverse)
btn_arm_reverse.grid(row=2,column=1, ipadx=6,ipady=6,padx=5,pady=5)

btn_elevator_forward =tk.Button(root, text="Elevator Up",command=move_elevator_forward)
btn_elevator_forward.grid(row=3,column=0, ipadx=6,ipady=6,padx=5,pady=5)

btn_elevator_reverse =tk.Button(root, text="Elevator down",command=move_elevator_reverse)
btn_elevator_reverse.grid(row=3,column=1, ipadx=6,ipady=6,padx=5,pady=5)

btn_wrist_forward =tk.Button(root, text="Wrist move",command=move_wrist_forward)
btn_wrist_forward.grid(row=4,column=0, ipadx=6,ipady=6,padx=5,pady=5)

btn_wrist_reverse =tk.Button(root, text="Wrist rev",command=move_wrist_reverse)
btn_wrist_reverse.grid(row=4,column=1, ipadx=6,ipady=6,padx=5,pady=5)

button1 = tk.Button(root, text="Обдув/Присоска", command=toggle_logic)
button1.grid(row=5,column=0, ipadx=6,ipady=6,padx=5,pady=5)

button2 = tk.Button(root, text="Подать клей/Перестать подавать клей", command=toggle_logic2)
button2.grid(row=5,column=1, ipadx=6,ipady=6,padx=5,pady=5)

label1 = tk.Label(root, text="X:")
label1.grid(row=6,column=0, ipadx=6,ipady=6,padx=5,pady=5)

# Создаем поле ввода 1 (entry)
entry1 = tk.Entry(root, width=30)
entry1.grid(row=6,column=1, ipadx=6,ipady=6,padx=5,pady=5)

label2 = tk.Label(root, text="Y:")
label2.grid(row=7,column=0, ipadx=6,ipady=6,padx=5,pady=5)

# Создаем поле ввода 2 (entry)
entry2 = tk.Entry(root, width=30)
entry2.grid(row=7,column=1, ipadx=6,ipady=6,padx=5,pady=5)

# Создаем кнопку
button = tk.Button(root, text="Получить координаты", command=get_input)
button.grid(row=8,column=0, ipadx=6,ipady=6,padx=5,pady=5)
# Создаем метку для вывода результата
output_label = tk.Label(root, text="")
output_label.grid(row=8,column=1, ipadx=6,ipady=6,padx=5,pady=5)
arduino.write(b'feed')
response = arduino.readline()
decoded_response = response.decode('utf-8')

root.mainloop()