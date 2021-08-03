from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QAction, QMessageBox
import sys
from ui import Ui_MainWindow
from time import time, sleep
from threading import Thread
import os
from cortex import Cortex, SUB_REQUEST_ID
from csv import writer
import json
from playsound import playsound
import socket

running = True
data_stream_running = False

start_time = time()
data_stream = None
clunch_soundpath = 'static/clunch_signal.wav'
relax_soundpath = 'static/relax_sound.wav'

last_stream_timestamp = None

serverMACAddress = '00:18:E4:34:BF:A1'
port = 1

user = {"license": "2ae1902e-dae0-484f-813b-e0fb06436fb5",
        "client_id": "hwfSzYMfKg2YIx5Fbq6OuYqO2vXsa79vkRkROdeH",
        "client_secret": "5IpS0IjWBd8BVFOm4jtj5fQKE7YBYF23KX3uiHEQsdaJdvHS5mx3kXDcQXtfD1pzDlzxnm2b39cujOGO44Pwgf3QKsscaOxsNnSh8JWEFH8izk8ENzIuch8sspdkOTp7",
        "debit": 100}

'''{'id': 6, 'jsonrpc': '2.0',
 'result': {'failure': [], 'success': [{'cols':
  ['COUNTER', 'INTERPOLATED', 'AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4', 'RAW_CQ', 'MARKER_HARDWARE', 'MARKERS'], 'sid': '013f2c0b-8dfb-4fc0-a2ef-92332d8711da', 'streamName': 'eeg'}]}}'''


def write_stream_to_file(window, data_filename):
    global last_stream_timestamp, emotiv_api
    emotiv_api = Cortex(user, debug_mode=True)
    emotiv_api.do_prepare_steps()
    print(emotiv_api)
    sleep(2.)
    data_stream = emotiv_api.sub_request(['eeg'])
    with open(data_filename, mode='w', encoding='utf-8', newline='') as csv_file:
        data_writer = writer(csv_file, delimiter=',')
        while running and window.data_stream_active:
            new_data = json.loads(data_stream.recv())
            if 'id' in new_data.keys() and new_data['id'] == SUB_REQUEST_ID:
                counter, interpolated, *sensors, raw_cq, _, _ = new_data['result']['success'][0]['cols']
                new_row = [0., 0., interpolated, *sensors, raw_cq]
                data_writer.writerow(new_row)
            else:
                counter, interpolated, *sensors, raw_cq, _, _ = new_data['eeg']
                new_timestamp = new_data['time']
                new_row = [new_timestamp, 0., interpolated, *sensors, raw_cq]
                data_writer.writerow(new_row)
                last_stream_timestamp = new_timestamp
    emotiv_api.unsub_request(['eeg'])


def reset_timer():
    global start_time
    start_time = time()


def update_time(window):
    while running:
        window.label_3.setText("{:10.1f}".format(time() - start_time))
        sleep(0.01)


arduino_serial = None


def init_serial():
    return
    global arduino_serial
    try:
        arduino_serial = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        arduino_serial.connect((serverMACAddress, port))
    except Exception as e:
        print(e)
        raise ConnectionError


def send_finger_states(window):
    tags = window.get_tags()
    res_str = ''
    for tag in tags[2:]:
        if tag == 1:
            if round(tags[0]) == 1:
                res_str += str(abs(round(tag) - 1))
            else:
                res_str += str(round(tag))
        else:
            res_str += '1'
    try:
        res_str = res_str[::-1]
        arduino_serial.send(res_str.encode('utf-8'))
        print(res_str)
    except Exception as e:
        print(e)
        raise ValueError


start_timestamp = None


def motion_loop_threading(window):
    global start_timestamp
    # TODO loop with sound Thread and motions
    # call write_new_timestamp to save last timestamp
    global start_time
    loop_num = int(window.spinBox.text())
    i = 0
    start_time = time()
    while i < loop_num and window.motion_loop_running:
        if window.checkBox_6.isChecked():
            start_time = time()
        window.label.setText(f'Текущее повторение №{i + 1}')
        # start_motion, save timestamp
        # stop_motion, write_new_timestamp

        # play signal
        print(f'signal start at {time()}')
        if window.radioButton.isChecked():
            Thread(target=playsound, args=(clunch_soundpath,)).start()
        else:
            Thread(target=playsound, args=(relax_soundpath,)).start()
        sleep(1.)
        Thread(target=send_finger_states, args=(window,)).start()
        start_timestamp = last_stream_timestamp
        sleep(1.)
        print('signal stop')
        window.write_new_timestamp(start_timestamp)
        # invert radiobuttons
        if window.radioButton.isChecked():
            window.radioButton_2.setChecked(True)
        else:
            window.radioButton.setChecked(True)
        app.processEvents()
        sleep(2.)
        i += 1
    window.label.setText('Нет повторений')


def blink_threading(window):
    global start_time
    start_time = time()
    print('starting blink sample')
    Thread(target=playsound, args=(clunch_soundpath,)).start()
    sleep(1.)
    begin_time = last_stream_timestamp
    sleep(2.)
    window.write_new_timestamp(start_timestamp=begin_time, blinking=True)
    window.pushButton_5.setText('Готово')
    window.pushButton_5.setEnabled(False)


def calm_eeg_threading(window):
    global start_time
    start_time = time()
    print('starting calm EEG sample')
    Thread(target=playsound, args=(clunch_soundpath,)).start()
    sleep(1.)
    begin_time = last_stream_timestamp
    sleep(20.)
    window.write_new_timestamp(start_timestamp=begin_time, calm_eeg=True)
    window.pushButton_6.setText('Готово')
    window.pushButton_6.setEnabled(False)


def test_sound_loop_threading(window):
    for i in range(7):
        sound_path = clunch_soundpath if i % 2 == 0 else relax_soundpath
        Thread(target=playsound, args=(sound_path,)).start()
        sleep(1.)
        sleep(2.)
        if not running:
            break


def relax_all():
    global arduino_serial
    try:
        arduino_serial.send('11111'.encode('utf-8'))
    except Exception as e:
        print(e)
        raise ValueError


class BrainForceRecordApp(QMainWindow, Ui_MainWindow):
    data_filename = '/main_record.csv'
    timelog_filename = '/timelog.csv'

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUI()
        self.filepath = None
        self.data_stream_active = False
        self.timestamp_file = None
        self.motion_loop_running = False
        init_serial()

    def initUI(self):
        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)
        Thread(target=update_time, args=(self,)).start()

        self.radioButton.setChecked(True)
        self.pushButton_3.clicked.connect(self.choose_filename)
        self.pushButton_4.clicked.connect(reset_timer)
        self.pushButton.clicked.connect(self.start_stream_writer)
        self.pushButton_2.clicked.connect(self.switch_motion_loop)
        self.pushButton_5.clicked.connect(self.blink)
        self.pushButton_6.clicked.connect(self.calm_eeg)
        self.pushButton_7.clicked.connect(self.test_clunch_sound)
        self.pushButton_8.clicked.connect(self.test_relax_sound)
        self.pushButton_9.clicked.connect(self.test_sound_loop)
        self.pushButton_10.clicked.connect(relax_all)

        self.show()

    def test_clunch_sound(self):
        Thread(target=playsound, args=(clunch_soundpath,)).start()

    def test_sound_loop(self):
        Thread(target=test_sound_loop_threading, args=(self,)).start()

    def test_relax_sound(self):
        Thread(target=playsound, args=(relax_soundpath,)).start()

    def blink(self):
        Thread(target=blink_threading, args=(self,)).start()

    def calm_eeg(self):
        Thread(target=calm_eeg_threading, args=(self,)).start()

    def start_stream_writer(self):
        print('starting stream writer')
        if self.check_filepath() and not self.data_stream_active:
            self.data_stream_active = True
            self.data_thread = Thread(target=write_stream_to_file, args=(self, self.lineEdit.text())).start()
            self.pushButton.setText('Закончить исследование')
            full_timelog_path = '/'.join(
                self.lineEdit.text().split('/')[:-1]) + BrainForceRecordApp.timelog_filename
            print(full_timelog_path)
            if os.path.isfile(full_timelog_path):
                print('file already exists')
            self.timestamp_file = open(full_timelog_path, mode='w', encoding='utf-8', newline='')
            self.timestamp_writer = writer(self.timestamp_file, delimiter=',')
            self.timestamp_writer.writerow(['start_timestamp', 'stop_timestamp',
                                            'clunch', 'relax', 'thumb', 'index',
                                            'middle', 'ring', 'pinky'])
        elif self.data_stream_active:
            print('stopping stream writer')
            self.data_stream_active = False
            sleep(0.5)
            self.timestamp_file.close()
            self.pushButton.setText('Начать исследование')
            # add reset values?

    def check_filepath(self):
        path_to_file = self.lineEdit.text()
        if self.data_stream_active and not path_to_file or \
                not os.path.isdir('/'.join(path_to_file.split('/')[:-1])) or \
                os.path.isfile(path_to_file):
            box_reply = QMessageBox.question(self, 'Done', "Check CSV files, recording",
                                             QMessageBox.Apply, QMessageBox.Apply)
            return False
        return True

    def switch_motion_loop(self):
        if self.motion_loop_running:
            print('stopping motion loop')
            self.motion_loop_running = False
            sleep(0.5)
            self.pushButton_2.setText('Начать цикл')
        else:
            print('starting motion loop')
            self.pushButton_2.setText('Остановить цикл')
            self.motion_loop_running = True
            Thread(target=motion_loop_threading, args=(self,)).start()

    def get_tags(self):
        tags = [0] * 7  # for open, close and 5 fingers
        if self.radioButton.isChecked():
            tags[0] = 1
        elif self.radioButton_2.isChecked():
            tags[1] = 1
        if self.checkBox.isChecked():
            tags[2] = 1
        if self.checkBox_2.isChecked():
            tags[3] = 1
        if self.checkBox_3.isChecked():
            tags[4] = 1
        if self.checkBox_4.isChecked():
            tags[5] = 1
        if self.checkBox_5.isChecked():
            tags[6] = 1
        return tags

    def write_new_timestamp(self, start_timestamp, blinking=False, calm_eeg=False):
        # if [0, 0...] => blinking sample
        # if [1, 1...] => calm eeg sample
        timestamp_to_save = last_stream_timestamp
        # [going down, going up, thumb, index, middle, ring, pinky]
        # [0, 1, 0, 0, 1, 1, 0] is relaxing from spiderman gesture (ring and middle fingers down)
        tags = [0] * 7  # for open, close and 5 fingers
        if blinking:
            new_csv_row = [start_timestamp, timestamp_to_save, *tags]
            print(new_csv_row)
            self.timestamp_writer.writerow(new_csv_row)
            return
        if calm_eeg:
            tags[0] = 1
            tags[1] = 1
            new_csv_row = [start_timestamp, timestamp_to_save, *tags]
            print(new_csv_row)
            self.timestamp_writer.writerow(new_csv_row)
            return
        if self.radioButton.isChecked():
            tags[0] = 1
        elif self.radioButton_2.isChecked():
            tags[1] = 1
        if self.checkBox.isChecked():
            tags[2] = 1
        if self.checkBox_2.isChecked():
            tags[3] = 1
        if self.checkBox_3.isChecked():
            tags[4] = 1
        if self.checkBox_4.isChecked():
            tags[5] = 1
        if self.checkBox_5.isChecked():
            tags[6] = 1
        new_csv_row = [start_timestamp, timestamp_to_save, *tags]
        print(new_csv_row)
        self.timestamp_writer.writerow(new_csv_row)

    def closeEvent(self, event):
        global running, arduino_serial
        self.data_stream_active = False
        self.motion_loop_running = False
        running = False
        arduino_serial.close()
        sleep(1.)
        event.accept()

    def choose_filename(self):
        directory = QFileDialog.getExistingDirectory(self, "title", "")
        filename = directory + BrainForceRecordApp.data_filename
        print(f'new filename is {filename}')
        if os.path.isfile(filename) or os.path.isfile(directory + BrainForceRecordApp.timelog_filename):
            button_reply = QMessageBox.question(self, 'Warning',
                                                "Files already exist! Change directory or type manually",
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if button_reply == QMessageBox.Yes:
                self.lineEdit.setText(directory + '/...')
            else:
                self.lineEdit.clear()
        else:
            self.lineEdit.setText(filename)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = BrainForceRecordApp()
    try:
        sys.exit(app.exec())
    finally:
        arduino_serial.close()
