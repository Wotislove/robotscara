#include <AccelStepper.h>

// Определяем пины для шагового двигателя
#define STEP_HAND_PIN 3
#define DIR_HAND_PIN 6
#define LIMIT_SWITCH_PIN A3
#define LIMIT_SWITCH2_PIN A0// Пин для концевого выключателя
#define LIMIT_SWITCH3_PIN A1
#define STEP_ARM_PIN 2
#define DIR_ARM_PIN 5
#define STEP_ELEVATOR_PIN 12
#define DIR_ELEVATOR_PIN 13
#define DIR_WRIST_PIN 7
#define STEP_WRIST_PIN 4
#define LIMIT_SWITCH4_PIN 9

// Создаем объект AccelStepper
AccelStepper stepperhand(AccelStepper::DRIVER, STEP_HAND_PIN, DIR_HAND_PIN);
AccelStepper stepperarm(AccelStepper::DRIVER, STEP_ARM_PIN, DIR_ARM_PIN);
AccelStepper stepperelevator(AccelStepper::DRIVER,STEP_ELEVATOR_PIN, DIR_ELEVATOR_PIN);
AccelStepper stepperwrist(AccelStepper::DRIVER, STEP_WRIST_PIN, DIR_WRIST_PIN);
bool moveForward = false;
bool moveReverse = false;
bool moveToHome = false;
bool stopMotor = false;
bool moveArmReverse=false;
bool moveArmForward=false;
bool moveToHomeArm = false;
int a=0;
int b=0;
bool ElevatorUp=false;
bool ElevatorDown=false;
bool moveToHomeElevator=false;
int c=0;
bool moveWristForward=false;
bool moveWristReverse=false;
bool moveToHomeWrist=false;
int d=0;
void setup() {
  pinMode(LIMIT_SWITCH_PIN, INPUT); // Устанавливаем пин для концевого выключателя
  pinMode(LIMIT_SWITCH2_PIN, INPUT); // Устанавливаем пин для концевого выключателя
  pinMode(LIMIT_SWITCH3_PIN,INPUT);
  pinMode(LIMIT_SWITCH4_PIN,INPUT);
  stepperhand.setMaxSpeed(4000); // Устанавливаем максимальную скорость
  stepperhand.setAcceleration(2000); // Устанавливаем ускорение
  stepperarm.setMaxSpeed(4000);
  stepperarm.setAcceleration(2000);
  stepperelevator.setMaxSpeed(4000);
  stepperelevator.setAcceleration(2000);
  stepperwrist.setMaxSpeed(4000);
  stepperwrist.setAcceleration(2000);
  Serial.begin(9600); // Инициализация последовательного порта
}

void loop() {
  if (Serial.available() > 0){
    char command = Serial.read();
    switch (command){
      case 'F':
        moveForward = true;
        moveReverse = false;
        moveToHome = false;
        stopMotor = false;
        moveArmReverse=false;
        moveArmForward=false;
        ElevatorDown=false;
        ElevatorUp=false;
        moveToHomeElevator=false;
        moveWristForward=false;
        moveWristReverse=false;
        moveToHomeWrist=false;
        break;
      case 'R':
        moveForward = false;
        moveReverse = true;
        moveToHome = false;
        stopMotor = false;
        moveArmReverse=false;
        moveArmForward=false;
        ElevatorDown=false;
        ElevatorUp=false;
        moveToHomeElevator=false;
        moveWristForward=false;
        moveWristReverse=false;
        moveToHomeWrist=false;
        break;
      case 'H':
        moveForward = false;
        moveReverse = false;
        moveToHome = true;
        stopMotor = false;
        moveArmReverse=false;
        moveArmForward=false;
        stopMotor = false;
        moveToHomeArm = true;
        moveToHomeElevator=true;
        moveToHomeWrist=true;
        ElevatorDown=false;
        ElevatorUp=false;
        moveWristForward=false;
        moveWristReverse=false;
        break;
      case 'S':
        moveForward = false;
        moveReverse = false;
        moveToHome = false;
        stopMotor = true;
        moveArmReverse=false;
        moveArmForward=false;
        ElevatorDown=false;
        ElevatorUp=false;
        moveToHomeElevator=false;
        moveWristForward=false;
        moveWristReverse=false;
        moveToHomeWrist=false;
        break;
      case 'Z':
        moveArmReverse=true;
        moveArmForward=false;
        moveForward = false;
        moveReverse = false;
        moveToHome = false;
        stopMotor = false;
        ElevatorDown=false;
        ElevatorUp=false;
        moveToHomeElevator=false;
        moveWristForward=false;
        moveWristReverse=false;
        moveToHomeWrist=false;
        break;
      case 'X':
        moveArmReverse=false;
        moveArmForward=true;
        moveForward = false;
        moveReverse = false;
        stopMotor = false;
        moveToHome = false;
        ElevatorDown=false;
        ElevatorUp=false;
        moveToHomeElevator=false;
        moveWristForward=false;
        moveWristReverse=false;
        moveToHomeWrist=false;
        break;
      case 'C':
        moveArmReverse=false;
        moveForward = false;
        moveReverse = false;
        stopMotor = false;
        moveToHome = false;
        moveArmForward=true;
        ElevatorDown=false;
        ElevatorUp=false;
        moveToHomeElevator=false;
        moveWristForward=false;
        moveWristReverse=false;
        moveToHomeWrist=false;
        break;
      case 'U':
        ElevatorUp=true;
        ElevatorDown=false;
        moveArmReverse=false;
        moveForward = false;
        moveReverse = false;
        stopMotor = false;
        moveToHome = false;
        moveArmForward=false;
        moveToHomeElevator=false;
        moveWristForward=false;
        moveWristReverse=false;
        moveToHomeWrist=false;
        break;
      case 'D':
        ElevatorDown=true;
        ElevatorUp=false;
        moveArmReverse=false;
        moveForward = false;
        moveReverse = false;
        stopMotor = false;
        moveToHome = false;
        moveArmForward=false;
        moveToHomeElevator=false;
        moveWristForward=false;
        moveWristReverse=false;
        moveToHomeWrist=false;
        break;
      case 'V':
        moveWristForward=true;
        moveWristReverse=false;
        moveToHomeWrist=false;
        ElevatorDown=false;
        ElevatorUp=false;
        moveArmReverse=false;
        moveForward = false;
        moveReverse = false;
        stopMotor = false;
        moveToHome = false;
        moveArmForward=false;
        moveToHomeElevator=false;
        break;
      case 'B':
        moveWristForward=false;
        moveWristReverse=true;
        moveToHomeWrist=false;
        ElevatorDown=false;
        ElevatorUp=false;
        moveArmReverse=false;
        moveForward = false;
        moveReverse = false;
        stopMotor = false;
        moveToHome = false;
        moveArmForward=false;
        moveToHomeElevator=false;
      break;
    }
  }
  if(moveForward && a == 0){
    stepperhand.setSpeed(-1000);
    stepperhand.runSpeed();
  }
  else if (moveReverse){
    stepperhand.setSpeed(1000);
    stepperhand.runSpeed();
    a=0;
  }
  else if (moveToHome && a == 0){
    stepperhand.setSpeed(-1000);
    stepperhand.runSpeed();
  }
  else if (moveToHomeArm && b==0){
    stepperarm.setSpeed(-1000);
    stepperarm.runSpeed();
  }else if (moveArmForward && b==0){
    stepperarm.setSpeed(-1000);
    stepperarm.runSpeed();
  }
  else if (moveArmReverse){
    stepperarm.setSpeed(1000);
    stepperarm.runSpeed();
    b=0;
  }
  else if (ElevatorUp && c == 0){
    stepperelevator.setSpeed(1000);
    stepperelevator.runSpeed();
  }
  else if(ElevatorDown){
    stepperelevator.setSpeed(-1000);
    stepperelevator.runSpeed();
    c=0;
  }
  else if(moveToHomeElevator && c == 0){
    stepperelevator.setSpeed(1000);
    stepperelevator.runSpeed();
  }
  else if(moveToHomeWrist && d == 0){
    stepperwrist.setSpeed(-1000);
    stepperwrist.runSpeed();
  }
  else if (moveWristReverse){
    stepperwrist.setSpeed(1000);
    stepperwrist.runSpeed();
    d=0;
  }
  else if (moveWristForward && d==0){
    stepperwrist.setSpeed(-1000);
    stepperwrist.runSpeed();
  }
  if (analogRead(LIMIT_SWITCH_PIN)>500){
    stepperhand.stop();
    moveForward = false;
    moveToHome = false;
    a=1;
  }
  if (analogRead(LIMIT_SWITCH2_PIN)>500){
    stepperarm.stop();
    moveArmForward = false;
    moveToHomeArm = false;
    b=1;
  }
  if (analogRead(LIMIT_SWITCH3_PIN)>500){
    stepperelevator.stop();
    ElevatorUp=false;
    moveToHomeElevator=false;
    c=1;
  }
  if (digitalRead(LIMIT_SWITCH4_PIN)==1){
    stepperwrist.stop();
    moveToHomeWrist=false;
    moveWristForward=false;
    d=1;
  }
  else if (stopMotor){
    stepperhand.stop();
    stepperarm.stop();
    stepperelevator.stop();
    stepperwrist.stop();
  }
  stepperhand.run();
  stepperwrist.run();
  stepperarm.run();
  stepperelevator.run();
}