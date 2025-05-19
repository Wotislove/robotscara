#include <ArduinoJson.h>
#include <Servo.h>

const uint8_t ENDSTOP_PINS[4] = {A10, A9, A11, A12};
const uint8_t STEP_PINS[4] = {60, 54, 26, 36};
const uint8_t DIR_PINS[4] = {61, 55, 28, 34};
const uint8_t ENABLE_PINS[4] = {56, 38, 24, 30};
const int VALVE_PINS[2] = {5, 6}, SERVO_PIN = 11;

const uint16_t MOTOR_CONFIGS[4][4] = {
  {300, 1, 100, 100000*3}, {500, 1, 50, 100000*3},
  {500, 1, 150, 100000*3}, {500, 0, 80, 100000*3}
};

const char* SENSOR_NAMES[4] = {"SENSOR:верхний", "SENSOR:нижний", "SENSOR:руки", "SENSOR:кисти"};
const float ENDSTOP_TRIGGER_VOLTAGE = 0.5;
const unsigned long DEBOUNCE_DELAY = 50;

Servo servo;
bool motorStates[4] = {0}, lastStableState[4] = {0}, lastReportedState[4] = {0}, systemActive = true;
uint32_t motorSteps[4] = {0}, stepsToEndstop[4] = {0};
unsigned long lastDebounceTime[4] = {0};
uint8_t currentMotor = 0;

void setup() {
  Serial.begin(9600);
  while (!Serial);
  while (Serial.available()) Serial.read();

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  for (int i = 0; i < 4; i++) {
    pinMode(ENDSTOP_PINS[i], INPUT);
    pinMode(STEP_PINS[i], OUTPUT);
    pinMode(DIR_PINS[i], OUTPUT);
    pinMode(ENABLE_PINS[i], OUTPUT);
    digitalWrite(ENABLE_PINS[i], HIGH);
    lastStableState[i] = lastReportedState[i] = isEndstopTriggered(i);
    printEndstopState(i);
  }

  pinMode(VALVE_PINS[0], OUTPUT);
  pinMode(VALVE_PINS[1], OUTPUT);
  digitalWrite(VALVE_PINS[0], LOW);
  digitalWrite(VALVE_PINS[1], LOW);
  
  Serial.println("Система готова. Ожидание команд...");
}

void loop() {
  checkEndstopChanges();
  
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    processCommand(input);
  }

  if (systemActive && !allEndstopsTriggered()) {
    runCurrentMotor();
    if (motorStates[currentMotor]) {
      printMotorInfo(currentMotor);
      currentMotor = (currentMotor + 1) % 4;
      delay(500);
    }
  }
}

void processCommand(const String& input) {
  if (input.startsWith("{")) processJsonCommand(input);
  else if (input.length() > 0) processTextCommand(input);
}

void processJsonCommand(const String& jsonCommand) {
  StaticJsonDocument<200> doc;
  if (deserializeJson(doc, jsonCommand)) return sendError("Invalid JSON");
  if (doc["command"] == "HOME") executeHomeCommand();
}

void processTextCommand(const String& cmd) {
  if (cmd.startsWith("m") && cmd.length() >= 3) {
    uint8_t m = cmd.charAt(1) - '0', d = cmd.charAt(2) - '0';
    if (m <= 3) d == 0 ? stop_motor(m) : start_motor(m, d == 1 ? HIGH : LOW);
  } else if (cmd == "e") { 
    digitalWrite(VALVE_PINS[0], HIGH); digitalWrite(VALVE_PINS[1], HIGH);
    Serial.println("Присоска включена (оба клапана)");
  } else if (cmd == "r") {
    digitalWrite(VALVE_PINS[0], LOW); digitalWrite(VALVE_PINS[1], HIGH);
    Serial.println("Дозатор включен (только D6)");
  } else if (cmd == "x") {
    digitalWrite(VALVE_PINS[0], LOW); digitalWrite(VALVE_PINS[1], LOW);
    Serial.println("Вся пневматика выключена");
  } else if (cmd == "q") {
    servo.attach(SERVO_PIN); servo.write(90);
    Serial.println("Сервопривод включен (90 градусов)");
  } else if (cmd == "w") {
    servo.detach();
    Serial.println("Сервопривод выключен");
  } else Serial.println("Неизвестная команда: " + cmd);
}

void start_motor(uint8_t m, uint8_t dir) {
  digitalWrite(ENABLE_PINS[m], LOW);
  digitalWrite(DIR_PINS[m], dir);
  for (int i = 0; i < 100; i++) {
    digitalWrite(STEP_PINS[m], HIGH);
    delayMicroseconds(500);
    digitalWrite(STEP_PINS[m], LOW);
    delayMicroseconds(500);
  }
}

void stop_motor(uint8_t m) { digitalWrite(ENABLE_PINS[m], HIGH); }

void executeHomeCommand() { 
  if (!systemActive) {
    systemActive = true;
    resetMotorStates();
    digitalWrite(LED_BUILTIN, LOW);
    Serial.println("Запуск движения...");
    sendResponse("success", "Home procedure started");
  } else sendError("System already active");
}

void checkEndstopChanges() { 
  for (int i = 0; i < 4; i++) {
    bool state = isEndstopTriggered(i);
    if (state != lastStableState[i]) lastDebounceTime[i] = millis();
    if ((millis() - lastDebounceTime[i]) > DEBOUNCE_DELAY && state != lastReportedState[i]) {
      lastStableState[i] = lastReportedState[i] = state;
      printEndstopState(i);
    }
    lastStableState[i] = state;
  }
}

void printEndstopState(uint8_t m) { 
  Serial.print(SENSOR_NAMES[m]); Serial.println(lastStableState[m] ? ":1" : ":0");
  if (m == 3 && lastStableState[m]) Serial.println("Концевик кисти вызвал остановку мотора 4");
}

bool isEndstopTriggered(uint8_t m) { 
  return analogRead(ENDSTOP_PINS[m]) * (5.0 / 1023.0) > ENDSTOP_TRIGGER_VOLTAGE;
}

void runCurrentMotor() { 
  uint8_t m = currentMotor;
  if (checkEndstopAndReport(m)) return motorStates[m] = true;
  
  digitalWrite(ENABLE_PINS[m], LOW);
  digitalWrite(DIR_PINS[m], MOTOR_CONFIGS[m][1]);
  
  for (int i = 0; i < MOTOR_CONFIGS[m][2]; i++) {
    if (checkEndstopAndReport(m)) return motorStates[m] = true, digitalWrite(ENABLE_PINS[m], HIGH);
    stepMotor(m, map(i, 0, MOTOR_CONFIGS[m][2], MOTOR_CONFIGS[m][0]*3, MOTOR_CONFIGS[m][0]));
    stepsToEndstop[m]++;
  }
  
  while (!checkEndstopAndReport(m)) {
    if (motorSteps[m]++ >= MOTOR_CONFIGS[m][3]) {
      motorStates[m] = true;
      Serial.print("Мотор "); Serial.print(m+1); Serial.println(": макс. шаги!");
      return digitalWrite(ENABLE_PINS[m], HIGH);
    }
    stepMotor(m, MOTOR_CONFIGS[m][0]);
    stepsToEndstop[m]++;
  }
  digitalWrite(ENABLE_PINS[m], HIGH);
}

bool checkEndstopAndReport(uint8_t m) { 
  if (isEndstopTriggered(m)) {
    if (m == 3 && !lastReportedState[m]) printEndstopState(m);
    return true;
  }
  return false;
}

void stepMotor(uint8_t m, uint16_t delayUs) { 
  digitalWrite(STEP_PINS[m], HIGH);
  delayMicroseconds(delayUs);
  digitalWrite(STEP_PINS[m], LOW);
  delayMicroseconds(delayUs);
}

bool allEndstopsTriggered() { 
  for (int i = 0; i < 4; i++) if (!motorStates[i] && !isEndstopTriggered(i)) return false;
  
  systemActive = false;
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("Все моторы достигли концевиков");
  sendResponse("success", "All endstops reached");
  return true;
}

void printMotorInfo(uint8_t m) { 
  Serial.print("Мотор "); Serial.print(m+1); Serial.print(" остановлен. Шагов: "); Serial.println(stepsToEndstop[m]);
}

void resetMotorStates() { 
  for (int i = 0; i < 4; i++) motorStates[i] = motorSteps[i] = stepsToEndstop[i] = 0;
  currentMotor = 0;
}

void sendError(const char* msg) { sendResponse("error", msg); }
void sendResponse(const char* status, const char* msg) {
  StaticJsonDocument<100> doc;
  doc["status"] = status; doc["message"] = msg;
  serializeJson(doc, Serial); Serial.println();
}