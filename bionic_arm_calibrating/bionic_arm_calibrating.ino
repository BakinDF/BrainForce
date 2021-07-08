#include <Servo.h> //подключаем библиотеку для работы с сервоприводами

#define THUMB_PIN 10
#define FOREFINGER_PIN 9
#define MIDDLEFINGER_PIN 6
#define RINGFINGER_PIN 5
#define LITTLEFINGER_PIN 3
const byte fingers[5] = {THUMB_PIN,
                         FOREFINGER_PIN,
                         MIDDLEFINGER_PIN,
                         RINGFINGER_PIN,
                         LITTLEFINGER_PIN};
#define THUMB_CLENCHED 0 //мизинец
#define FOREFINGER_CLENCHED 0 //безымянный
#define MIDDLEFINGER_CLENCHED 120 //средний
#define RINGFINGER_CLENCHED 120 //указательный
#define LITTLEFINGER_CLENCHED 0 //большой
#define THUMB_RELAXED 120
#define FOREFINGER_RELAXED 120
#define MIDDLEFINGER_RELAXED 0
#define RINGFINGER_RELAXED 0
#define LITTLEFINGER_RELAXED 120
const byte relaxed[5] = {THUMB_RELAXED,
                         FOREFINGER_RELAXED,
                         MIDDLEFINGER_RELAXED,
                         RINGFINGER_RELAXED,
                         LITTLEFINGER_RELAXED};
const byte clenched[5] = {THUMB_CLENCHED,
                         FOREFINGER_CLENCHED,
                         MIDDLEFINGER_CLENCHED,
                         RINGFINGER_CLENCHED,
                         LITTLEFINGER_CLENCHED};     
#define DELAY_A 10
Servo thumb;
Servo foreFinger;
Servo middleFinger;
Servo ringFinger;
Servo littleFinger;
Servo servos[5] = {thumb, foreFinger, middleFinger, ringFinger, littleFinger};

void setup() {
  byte i;
  for(i = 0; i < 5; i++) {
    (servos[i]).attach(fingers[i]);
    delay(DELAY_A);
  }
  for(i = 0; i < 5; i++) {
    servos[i].write(clenched[i]);
  }
}

void loop() {
  byte i;
  for(i = 0; i < 5; i++) {
    servos[i].write(relaxed[i]);
    delay(2000);
    servos[i].write(clenched[i]);
    delay(2000);
  }
}
