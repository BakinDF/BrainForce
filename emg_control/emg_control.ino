#include <Servo.h> //подключаем библиотеку для работы с сервоприводами


//задаем мин. и макс. угол поворота для каждого сервопривода,
//при необходимости их можно исправлять здесь
#define MAX_PINKY 120 //мизинец (пин 10) открыт
#define MIN_PINKY 0 //мизинец (пин 10) закрыт
#define MAX_RING_FINGER 120 //безымянный палец (пин 9) открыт
#define MIN_RING_FINGER 0 //безымянный палец (пин 9) закрыт
#define MAX_MIDDLE_FINGER 0 //средний палец (пин 6) закрыт
#define MIN_MIDDLE_FINGER 120 //средний палец (пин 6) открыт
#define MAX_INDEX_FINGER 0 //указательный палец (пин 5) закрыт
#define MIN_INDEX_FINGER 120 //указательный палец (пин 5) открыт
#define MAX_THUMB 120 //большой палец (пин 3) открыт
#define MIN_THUMB 0 //большой палец (пин 3) закрыт

//задаем скорости движения пальцев
//при необходимости их можно исправлять здесь
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

int t1,t2,t3,t4,t5 = 0; //переменные для хранения угла поворота сервы
int emg1, emg2 = 0; //переменные для хранения НЕобработанных значений ЭМГ-сигнала
int amp1, amp2 = 0; //переменные для хранения обработанных значений ЭМГ-сигнала
int threshhold1 = 30; //пеерменные для ранения пороговых значений
int threshhold2 = 30;
int min1, min2 = 255; //переменые для хранения минимальных значений обработанного сигнала
int max1, max2 = 0; //переменые для хранения максимальных значений обработанного сигнала


//функция вычисления амлитуды ЭМГ-сигнала
void calc_amp() {                                                
  for (int k = 0; k < 32; k++) {   
    emg1 = analogRead(A0);
    emg2 = analogRead(A1);                                                                  
    emg1 = map(emg1, 0, 1023, 0, 255);
    emg2 = map(emg2, 0, 1023, 0, 255);     
    if (emg1 > max1)                      
      max1 = emg1;                       
    if (emg1 < min1)                     
      min1 = emg1;  

    if (emg2 > max2)                      
      max2 = emg2;                       
    if (emg2 < min2)                     
      min2 = emg2; 
  }
  amp1 =  0.3*amp1 + 0.7*(max1 - min1); 
  amp2 =  0.3*amp2 + 0.7*(max2 - min2); 
  //при необходимости данные строчки можно раскомментировать для проверки значений с датчиков
  //Serial.print(amp1);
  //Serial.print("     "); 
  //Serial.println(amp2);               
  max1 = 0;                                  
  min1 = 255;  
  max2 = 0;                                  
  min2 = 255;                                 
}

void setup() {
 Serial.begin(9600);
 //указываем к каким контактам подключены сервоприводы
 servo_pinky.attach(10);
 servo_ring_finger.attach(9);
 servo_middle_finger.attach(6);
 servo_index_finger.attach(5);
 servo_thumb.attach(3);
 //проверка работоспособности - все пальцы на руке один раз сжимаются и разжимаются
 //цикл for выполняется 1 раз (если необходимо сделать несколько сжатий/разжатий, просто меняем условие: i < необходимое число)
 for (int i = 0; i < 2; i++){
 //все пальцы сжимаются, цикл while выполняется пока не достигнуты граничные значения угла поворота
 while (servo_pinky.read() > MIN_PINKY ||
 servo_ring_finger.read() > MIN_RING_FINGER || 
 servo_middle_finger.read() < MIN_MIDDLE_FINGER ||
 servo_index_finger.read() < MIN_INDEX_FINGER ||
 servo_thumb.read() > MIN_THUMB){
 //управление валом каждого сервопривода, знак + или - означает в какую сторону поворачивается вал
 t1 = servo_pinky.read() - SPEED_PINKY;
 servo_pinky.write(t1);
 t2 = servo_ring_finger.read() - SPEED_RING_FINGER;
 servo_ring_finger.write(t2);
 t3 = servo_middle_finger.read() - SPEED_MIDDLE_FINGER;
 servo_middle_finger.write(t3);
 t4 = servo_index_finger.read() + SPEED_INDEX_FINGER;
 servo_index_finger.write(t4);
 t5 = servo_thumb.read() - SPEED_THUMB;
 servo_thumb.write(t5);
 delay(15);
 }
 //все пальца разжимаются, цикл while выполняется пока не достигнуто граничное значения угла поворота
 while (servo_pinky.read() < MAX_PINKY ||
 servo_ring_finger.read() < MAX_RING_FINGER || 
 servo_middle_finger.read() > MAX_MIDDLE_FINGER||
 servo_index_finger.read() > MAX_INDEX_FINGER ||
 servo_thumb.read() < MAX_THUMB){
 //управление валом каждого сервопривода, знак + или - означает в какую сторону поворачивается вал
 t1 = servo_pinky.read() + SPEED_PINKY;
 servo_pinky.write(t1);
 t2 = servo_ring_finger.read() + SPEED_RING_FINGER;
 servo_ring_finger.write(t2);
 t3 = servo_middle_finger.read() + SPEED_MIDDLE_FINGER;
 servo_middle_finger.write(t3);
 t4 = servo_index_finger.read() - SPEED_INDEX_FINGER;
 servo_index_finger.write(t4);
 t5 = servo_thumb.read() + SPEED_THUMB;
 servo_thumb.write(t5);
 delay(15);
 }
 }
}

void loop() {
  //вызываем функцию для вычисления амилитуды ЭМГ сигнала для двух датчиков
  unsigned long start_time = millis();
  calc_amp();
  
  //если обе мышцы напряжены (значения амплитуд больше пороговых значений)
  if (amp1 > threshhold1 && amp2 > threshhold2){
    //реализуем жест кулак - все пальцы прижаты к ладони
    //поворачиваем каждый сервопривод для реализации жеста
    //при этом углы поворота не должны выходить за мин. и макс. значения
    if (servo_pinky.read() > MIN_PINKY){
      t1 = servo_pinky.read() - SPEED_PINKY;
      servo_pinky.write(t1);
    }
    if (servo_ring_finger.read() > MIN_RING_FINGER){
      t2 = servo_ring_finger.read() - SPEED_RING_FINGER;
      servo_ring_finger.write(t2);
    }
    if(servo_middle_finger.read() < MIN_MIDDLE_FINGER){
      t3 = servo_middle_finger.read() - SPEED_MIDDLE_FINGER;
      servo_middle_finger.write(t3);
    }
    if (servo_index_finger.read() < MIN_INDEX_FINGER){
      t4 = servo_index_finger.read() + SPEED_INDEX_FINGER;
      servo_index_finger.write(t4);
    }
    if (servo_thumb.read() > MIN_THUMB){
      t5 = servo_thumb.read() - SPEED_THUMB;
      servo_thumb.write(t5);
    }          
  } 
  //если только 1 мышца напряжена (значение амплитуды больше порогового значения)
  else if (amp1 > threshhold1){
    //реализуем жест V - прижаты все, кроме указательного и среднего
    //поворачиваем каждый сервопривод для реализации жеста
    //при этом углы поворота не должны выходить за мин. и макс. значения
    if (servo_pinky.read() > MIN_PINKY){
      t1 = servo_pinky.read() - SPEED_PINKY;
      servo_pinky.write(t1);
    }
    if (servo_ring_finger.read() > MIN_RING_FINGER){
      t2 = servo_ring_finger.read() - SPEED_RING_FINGER;
      servo_ring_finger.write(t2);
    }
    if(servo_middle_finger.read() > MAX_MIDDLE_FINGER){
      t3 = servo_middle_finger.read() + SPEED_MIDDLE_FINGER;
      servo_middle_finger.write(t3);
    }
    if (servo_index_finger.read() > MAX_INDEX_FINGER){
      t4 = servo_index_finger.read() - SPEED_INDEX_FINGER;
      servo_index_finger.write(t4);
    }
    if (servo_thumb.read() > MIN_THUMB){
      t5 = servo_thumb.read() - SPEED_THUMB;
      servo_thumb.write(t5);
    }          
  }
  //если только 2 мышца напряжена (значение амплитуды больше порогового значения)
  else if (amp2 > threshhold2){
    //реализуем жест ОК - все пальцы разжаты, кроме большого и указательного
    //поворачиваем каждый сервопривод для реализации жеста
    //при этом углы поворота не должны выходить за мин. и макс. значения
    if (servo_pinky.read() < MAX_PINKY){
      t1 = servo_pinky.read() + SPEED_PINKY;
      servo_pinky.write(t1);
    }
    if (servo_ring_finger.read() < MAX_RING_FINGER){
      t2 = servo_ring_finger.read() + SPEED_RING_FINGER;
      servo_ring_finger.write(t2);
    }
    if(servo_middle_finger.read() > MAX_MIDDLE_FINGER){
      t3 = servo_middle_finger.read() + SPEED_MIDDLE_FINGER;
      servo_middle_finger.write(t3);
    }
    if (servo_index_finger.read() < MIN_INDEX_FINGER){
      t4 = servo_index_finger.read() + SPEED_INDEX_FINGER;
      servo_index_finger.write(t4);
    }
    if (servo_thumb.read() > MIN_THUMB){
      t5 = servo_thumb.read() - SPEED_THUMB;
      servo_thumb.write(t5);
    }       
  }
  //иначе - все пальцы остаются разжаты или разжимаются, в зависимости от текущего положения валов сервоприводов
  else{
    //реализуем жест ладонь - все пальцы разжаты
    //поворачиваем каждый сервопривод для реализации жеста
    //при этом углы поворота не должны выходить за мин. и макс. значения
    if (servo_pinky.read() < MAX_PINKY){
      t1 = servo_pinky.read() + SPEED_PINKY;
      servo_pinky.write(t1);
    }
    if (servo_ring_finger.read() < MAX_RING_FINGER){
      t2 = servo_ring_finger.read() + SPEED_RING_FINGER;
      servo_ring_finger.write(t2);
    }
    if(servo_middle_finger.read() > MAX_MIDDLE_FINGER){
      t3 = servo_middle_finger.read() + SPEED_MIDDLE_FINGER;
      servo_middle_finger.write(t3);
    }
    if (servo_index_finger.read() > MAX_INDEX_FINGER){
      t4 = servo_index_finger.read() - SPEED_INDEX_FINGER;
      servo_index_finger.write(t4);
    }
    if (servo_thumb.read() < MAX_THUMB){
      t5 = servo_thumb.read() + SPEED_THUMB;
      servo_thumb.write(t5);
    }
  }
  delay(10);
}
