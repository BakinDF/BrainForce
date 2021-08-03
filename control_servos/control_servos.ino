#include <Servo.h>

#define MAX_PINKY 120 //мизинец (пин 10) открыт
#define MIN_PINKY 0 //мизинец (пин 10) закрыт
#define MAX_RING_FINGER 120 //безымянный палец (пин 9) открыт
#define MIN_RING_FINGER 0 //безымянный палец (пин 9) закрыт
#define MAX_MIDDLE_FINGER 120 //средний палец (пин 6) закрыт
#define MIN_MIDDLE_FINGER 0 //средний палец (пин 6) открыт
#define MAX_INDEX_FINGER 40 //указательный палец (пин 5) закрыт
#define MIN_INDEX_FINGER 70 //указательный палец (пин 5) открыт
#define MAX_THUMB 120 //большой палец (пин 3) открыт
#define MIN_THUMB 0 //большой палец (пин 3) закрыт

int max_min_angles[] = {MAX_PINKY, MIN_PINKY,
                        MAX_RING_FINGER, MIN_RING_FINGER,
                        MAX_MIDDLE_FINGER, MIN_MIDDLE_FINGER,
                        MAX_INDEX_FINGER, MIN_INDEX_FINGER,
                        MAX_THUMB, MIN_THUMB};

//задаем скорости движения пальцев
//при необходимости их можно исправлять здесь
#define SPEED 2
#define SPEED_PINKY 2
#define SPEED_RING_FINGER 2
#define SPEED_MIDDLE_FINGER -2
#define SPEED_INDEX_FINGER 2
#define SPEED_THUMB 2

//создаем объекты для работы с каждым мотором
Servo servo_pinky; //большой палец (Сервопривод Tower Pro MG995, пин 10 на шилде)
Servo servo_ring_finger; //большой палец (Сервопривод Tower Pro MG995, пин 9 на шилде)
Servo servo_middle_finger; //указательный палец (Сервопривод Tower Pro MG995, пин 6 на шилде)
Servo servo_index_finger; //средний палец (Сервопривод Tower Pro MG995, пин 5 на шилде)
Servo servo_thumb; //безымянный и мизинец (Сервопривод Tower Pro MG995, пин 3 на шилде)

Servo servos[] = {servo_pinky, servo_ring_finger, servo_middle_finger, servo_index_finger, servo_thumb};
int angles[] = {MIN_PINKY, MIN_RING_FINGER, MIN_MIDDLE_FINGER, MIN_INDEX_FINGER, MIN_THUMB};

int t1,t2,t3,t4,t5 = 0; //переменные для хранения угла поворота сервы
int emg1, emg2 = 0; //переменные для хранения НЕобработанных значений ЭМГ-сигнала
int amp1, amp2 = 0; //переменные для хранения обработанных значений ЭМГ-сигнала
int threshhold1 = 30; //пеерменные для ранения пороговых значений
int threshhold2 = 30;
int min1, min2 = 255; //переменые для хранения минимальных значений обработанного сигнала
int max1, max2 = 0; //переменые для хранения максимальных значений обработанного сигнала

void update_servos(int loop_with_delay_num=1){
  int current_angle, new_angle;
  for(byte i=0; i<loop_with_delay_num; ++i){
   for(byte j=0; i<sizeof(servos)/sizeof(int); ++i){
    if (angles[j] < max_min_angles[j*2] && angles[j] > max_min_angles[j*2 + 1]){ // if servo can move any further
      current_angle = servos[j].read();
      if (current_angle < angles[j]) new_angle = current_angle + SPEED;
      else new_angle = current_angle - SPEED;
      servos[j].write(new_angle);
    }
   }
  }
}
void clunch(){
  while (servo_pinky.read() > MIN_PINKY ||
 servo_ring_finger.read() > MIN_RING_FINGER || 
 servo_middle_finger.read() < MIN_MIDDLE_FINGER ||
 servo_index_finger.read() < MIN_INDEX_FINGER ||
 servo_thumb.read() > MIN_THUMB){
 //управление валом каждого сервопривода, знак + или - означает в какую сторону поворачивается вал
 t1 = servo_pinky.read() - SPEED_PINKY * (int)(servo_pinky.read() > MIN_PINKY);
 servo_pinky.write(t1);
 t2 = servo_ring_finger.read() - SPEED_RING_FINGER * (int)(servo_ring_finger.read() > MIN_RING_FINGER);
 servo_ring_finger.write(t2);
 t3 = servo_middle_finger.read() + SPEED_MIDDLE_FINGER * (int)(servo_middle_finger.read() < MIN_MIDDLE_FINGER);
 servo_middle_finger.write(t3);
 t4 = servo_index_finger.read() + SPEED_INDEX_FINGER * (int)(servo_index_finger.read() < MIN_INDEX_FINGER);
 servo_index_finger.write(t4);
 t5 = servo_thumb.read() - SPEED_THUMB * (int)(servo_thumb.read() > MIN_THUMB);
 servo_thumb.write(t5);
 delay(15);
 }
}

void relax(){
  while (servo_pinky.read() < MAX_PINKY ||
 servo_ring_finger.read() < MAX_RING_FINGER || 
 servo_middle_finger.read() > MAX_MIDDLE_FINGER||
 servo_index_finger.read() > MAX_INDEX_FINGER ||
 servo_thumb.read() < MAX_THUMB){
 //управление валом каждого сервопривода, знак + или - означает в какую сторону поворачивается вал
 t1 = servo_pinky.read() + SPEED_PINKY * (int)(servo_thumb.read() > MIN_THUMB);
 servo_pinky.write(t1);
 t2 = servo_ring_finger.read() + SPEED_RING_FINGER * (int)(servo_ring_finger.read() < MAX_RING_FINGER);
 servo_ring_finger.write(t2);
 t3 = servo_middle_finger.read() - SPEED_MIDDLE_FINGER * (int)(servo_middle_finger.read() > MAX_MIDDLE_FINGER);
 servo_middle_finger.write(t3);
 t4 = servo_index_finger.read() - SPEED_INDEX_FINGER * (int)(servo_index_finger.read() > MAX_INDEX_FINGER);
 servo_index_finger.write(t4);
 t5 = servo_thumb.read() + SPEED_THUMB * (int)(servo_thumb.read() < MAX_THUMB);
 servo_thumb.write(t5);
 delay(15);
 }
}

void setup() {
  Serial.begin(9600);
 //указываем к каким контактам подключены сервоприводы
 servo_pinky.attach(10);
 servo_ring_finger.attach(9);
 servo_middle_finger.attach(6);
 servo_index_finger.attach(5);
 servo_thumb.attach(3);
 relax();

}

void loop() {
  /*int delay_millis = 1000;
  clunch();
  Serial.println("clunched");
  delay(delay_millis);
  relax();
  Serial.println("relaxed");
  delay(delay_millis);*/
  update_servos();
  delay(15);
  for(byte i=0; i < 5; ++i) Serial.println(String(servos[i].read()));
  Serial.println("");
}
