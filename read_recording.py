from csv import reader
import matplotlib.pyplot as plt
import numpy as np
import pickle
import os
import matplotlib.mlab as mlab
import pywt
import cv2


# main class for reading raw data from main_record.csv file
class DataReader:
    def __init__(self, filename):
        self.file = open(filename, mode='r', encoding='utf-8')
        self.reader = reader(self.file, delimiter=',')
        self.headings = next(self.reader)
        self.reader = list(self.reader)
        self.last_index = 0
        print(len(self.reader))

    def get_headings(self):
        return self.headings

    def close_file(self):
        self.file.close()

    def get_reader(self):
        return self.reader

    # returns all written data between from_time and to_time timestamps only for channels in sensor_indexes
    def read_from_to(self, from_time, to_time, sensors_indexes,
                     show_plot=False, save_index=True):
        sensor_data = []
        timestamps = []

        for i in range(len(sensors_indexes)):
            sensor_data.append([])
        first_timestamp = None
        # get first data line
        for row in range(self.last_index, len(self.reader)):
            # reading csv line
            timestamp, _, _, *sensors, raw_cq = map(float, self.reader[row])
            # print(sensors, raw_cq)
            if not first_timestamp:
                first_timestamp = timestamp
            if timestamp < from_time:
                continue
            timestamps.append(timestamp)
            for value_index in range(len(sensors_indexes)):
                sensor_data[value_index].append(float(self.reader[row][sensors_indexes[value_index]]))
            if timestamp >= to_time:
                if save_index:
                    self.last_index = row
                break
        sensor_data = np.array(sensor_data)
        # print(sensor_data)
        timestamps = np.array(timestamps)
        # debug visualisation not tested
        if show_plot:
            plt.figure('CSV data plot')
            for plt_data in sensor_data:
                plt.plot(timestamps - first_timestamp, plt_data)
                break
            plt.show()
        return first_timestamp, timestamps, sensor_data

    # method to calculate PSD for sensors, can be used with independent data
    # input_shape must be (num_of_sensors, num_of_values)
    # if show_plot is True: visualizing data (not tested)
    def get_spectr(self, sensors_data, show_plot=False):
        power_res = []
        freqs_res = []
        for row_index in range(sensors_data.shape[0]):
            if show_plot:
                power, freqs = plt.psd(sensors_data[row_index])
                plt.show()
            else:
                power, freqs = mlab.psd(sensors_data[row_index], NFFT=256)
                # uncomment to see num of freqs
                # print(len(power))
            power = 10 * np.log10(power[2:-2])  # [82:-1])
            # print(power[82:-1])
            # print(power.shape)
            # power = power[2:-2]
            freqs = freqs[2:-2] * 64  # [82:-1] * 64
            power_res.append(power)
            freqs_res.append(freqs)
        return freqs_res, power_res


# was used for statistics
# input data: raw_eeg_data and calculated PSD from raw_eeg_data
# returns two-dimensional array with statistics params for each sensor
def extract_spectr_statistics(raw_sample, spectr_sample, add_index=True):
    if len(raw_sample) != len(spectr_sample):
        raise ValueError('samples have different number of channels')
    # used to divide eeg rythms
    # TODO change ratio to multiply with current len of spectral freqs returned from get_spectr method
    borders = np.round(np.array([0, 4, 8, 14, 30, 50, 62]) * (125 / 65)).astype(int)
    res = []
    for chn in range(len(spectr_sample)):
        new_stat = []
        if add_index:
            # chn value
            new_stat.append(chn)
        # mean of raw eeg
        new_stat.append(np.mean(raw_sample[chn]))
        # mean of spectr
        new_stat.append(np.mean(spectr_sample[chn]))
        # mean of all rythms in spectr PSD
        for border_index in range(len(borders[:-1])):
            new_stat.append(np.mean(spectr_sample[chn][borders[border_index]:borders[border_index + 1]]))
        # index for each rythm
        for border_index in range(len(borders[:-1])):
            rythm_summ = np.sum(spectr_sample[chn][borders[border_index]:borders[border_index + 1]])
            spectr_summ = np.sum(spectr_sample[chn])
            new_stat.append(rythm_summ / spectr_summ)
        res.append(new_stat)
    return res


def wavelet_denoise(data):
    res = []
    for sensor_data in data:
        # Create wavelet object and define parameters
        w = pywt.Wavelet('db6')
        maxlev = pywt.dwt_max_level(len(sensor_data), w.dec_len)
        threshold = 0.3  # Threshold for filtering

        # Decompose into wavelet components, to the level selected:
        coeffs = pywt.wavedec(sensor_data, 'db6', level=maxlev)

        for i in range(1, len(coeffs)):
            # plt.subplot(maxlev, 1, i)
            # plt.plot(coeffs[i])
            coeffs[i] = pywt.threshold(coeffs[i], threshold * np.amax(coeffs[i]))
            # plt.plot(coeffs[i])

        datarec = pywt.waverec(coeffs, 'db6')
        # change or uncomment line to turn on or off the denoising
        # append datarec -- denoising ON
        # append sensor_data -- denoising OFF
        res.append(datarec)
        # res.append(sensor_data)
    return np.array(res)


# function to read, proccess and append to resulting array data from raw eeg recording
def proccess_protocol(dir_path, frontal_sensors, motor_sensors, modifiers, num=0,
                      debug=False, sensor_to_viz_id=None, finger_label_to_vis=None,
                      cut_raw_sample_num=None):
    try:
        interface = DataReader(f'{dir_path}/main_record.csv')
        time_log_file = open(f'{dir_path}/timelog.csv', mode='r',
                             encoding='utf-8')
        time_log_reader = reader(time_log_file, delimiter=',')
        time_log_heading = next(time_log_reader)
    except FileNotFoundError:
        print('ERROR File not found')
        print(dir_path)
        return
    # this vars will be replaced by eeg samples
    eye_blink_data, calm_eeg_data = None, None
    # python lists => np.ndarray => return values
    data = []
    labels_states = []
    labels_fingers = []
    single_labels = []
    raw_eeg_data = []

    was_clunch, was_relax = False, False
    try:
        relax_samples, clunch_samples = [], []
        stat_relax, stat_clunch, stat_spectr_relax, stat_spectr_clunch = [], [], [], []
        # plt.figure('spectr diff')
        for log_row in time_log_reader:
            # var to move eeg sample borders
            DELTA = 0.5
            start_timestamp, stop_timestamp, clunch, relax, *fingers = map(float, log_row)
            # moving borders before reading the eeg values
            start_timestamp -= DELTA
            stop_timestamp += DELTA
            if clunch + relax < 0.001:  # 0 and 0 => eye blinking
                if eye_blink_data:
                    print('eye blink already initialized')
                    raise ValueError
                _, eye_blink_timestamps, eye_blink_data = interface.read_from_to(start_timestamp, stop_timestamp,
                                                                                 frontal_sensors + motor_sensors)
                if debug:
                    print(eye_blink_data.shape)
            elif clunch + relax > 1.999:  # 1 and 1 => calm eeg
                if calm_eeg_data:
                    print('calm eeg already initialized')
                    raise ValueError
                _, calm_eeg_timestamps, calm_eeg_data = interface.read_from_to(start_timestamp, stop_timestamp,
                                                                               motor_sensors)
                print(calm_eeg_data.shape)
            elif not calm_eeg_data.any() and not eye_blink_data.any():
                print('no initial data found yet')
                continue
            else:
                # getting motor, then frontal data
                motor_start_timestamp, motor_timestamps, sample_motor_data = interface.read_from_to(
                    start_timestamp,
                    stop_timestamp,
                    motor_sensors,
                    save_index=False)
                begin_frontal_timestamp, frontal_timestamps, sample_frontal_data = interface.read_from_to(
                    start_timestamp,
                    stop_timestamp,
                    frontal_sensors,
                    save_index=(RAW_EEG not in modifiers))
                # reading raw eeg (not PSD) if flag is in modifiers
                if RAW_EEG in modifiers:
                    begin_raw_eeg_timestamp, raw_eeg_timestamps, sample_raw_eeg_data = interface.read_from_to(
                        start_timestamp,
                        stop_timestamp,
                        frontal_sensors + motor_sensors)
                    # mean_peaks_data = np.mean(sample_raw_eeg_data, axis=0)
                    peak_to_skip = False
                    # filtering peaks
                    for peak_data in sample_raw_eeg_data:
                        # if peak_data[peak_data > 4600.].any() or peak_data[peak_data < 4250.].any():
                        if peak_data[peak_data > 5000.].any() or peak_data[peak_data < 4000.].any():
                            # plt.plot(np.arange(len(peak_data)), peak_data)
                            print('skip peak')
                            peak_to_skip = True
                            break
                    if peak_to_skip:
                        if relax:
                            stat_clunch = stat_clunch[:-1]
                        else:
                            stat_relax = stat_relax[:-1]
                        continue
                    if cut_raw_sample_num is None:
                        cut_raw_sample_num = 200
                    if cut_raw_sample_num > sample_raw_eeg_data.shape[1]:
                        print(sample_raw_eeg_data.shape)
                        print('skip')
                        continue

                    # data_to_plot = np.mean(sample_raw_eeg_data, axis=0)
                    # print('shape is ', data_to_plot.shape)
                    # plt.plot(np.arange(data_to_plot.shape[0]), data_to_plot)

                if FILTER_PEAKS in modifiers:
                    # plt.figure()
                    # plt.plot(np.arange(sample_motor_data.shape[1]), sample_motor_data[0], color='black')
                    filtered_motor_data = wavelet_denoise(sample_motor_data)
                    filtered_frontal_data = wavelet_denoise(sample_frontal_data)
                    filtered_raw_eeg_data = wavelet_denoise(sample_raw_eeg_data)

                    # print('filtered data length is', filtered_data.shape)
                    # plt.plot(np.arange(filtered_data.shape[1]), filtered_data[0], color='red')

                # visualization of given sensor or sensor, NOT TESTED
                if debug and sensor_to_viz_id:
                    if sensor_to_viz_id in frontal_sensors:
                        n = frontal_sensors.index(sensor_to_viz_id)
                        freqs_res, power_res = interface.get_spectr(sample_frontal_data[n])
                        freq, power = freqs_res[0], power_res[0]
                    elif sensor_to_viz_id in motor_sensors:
                        n = motor_sensors.index(sensor_to_viz_id)
                        freqs_res, power_res = interface.get_spectr(sample_motor_data[n])
                        freq, power = freqs_res[0], power_res[0]
                    else:
                        raise ValueError('sensor to plot is invalid')
                    if finger_label_to_vis and sensor_to_viz_id:
                        if clunch and fingers == [1, 1, 0, 0, 0]:
                            plt.plot(freq, 10 * np.log10(power), color='red')
                            was_clunch = True
                        if relax and fingers == [1, 1, 0, 0, 0]:
                            plt.plot(freqs_res[n], 10 * np.log10(power_res[n]), color='black')
                            was_relax = True
                        if was_relax and was_clunch:
                            plt.show()
                            was_relax, was_clunch = False, False

                if FILTER_PEAKS in modifiers:
                    sample_freqs, sample_spectr = interface.get_spectr(filtered_motor_data)
                    if clunch or relax:
                        new_stat = extract_spectr_statistics(sample_raw_eeg_data,
                                                             sample_spectr - np.amin(sample_spectr))
                        if not any(fingers):  # calm sample
                            stat_relax.append(new_stat)
                            stat_spectr_relax.append(np.mean(sample_spectr, axis=0))
                        elif all(fingers):  # active sample
                            stat_clunch.append(new_stat)
                            stat_spectr_clunch.append(np.mean(sample_spectr, axis=0))
                        print(len(stat_clunch), len(stat_relax))
                        if len(stat_clunch) == len(stat_relax) == 222:
                            stat_clunch = np.array(stat_clunch)
                            stat_relax = np.array(stat_relax)
                            print('shape is', stat_clunch.shape)
                            mean_stat_clunch = np.mean(stat_clunch, axis=0)
                            print('new shape is', mean_stat_clunch.shape)
                            mean_stat_relax = np.mean(stat_relax, axis=0)
                            print('clunch mean stat')
                            inde = 0
                            for d in mean_stat_clunch:
                                print('\t'.join(map(lambda x: "{:10.2f}".format(x), d)))
                                print()
                                inde += 1
                            print('\n')
                            print('relax mean stat')
                            for d in mean_stat_relax:
                                print('\t'.join(map(lambda x: "{:10.2f}".format(x), d)))
                                print()
                            plt.figure('relax mean spectr')
                            plt.plot(sample_freqs[0], np.mean(stat_spectr_relax, axis=0))
                            # plt.figure('clunch mean spectr')
                            plt.plot(sample_freqs[0], np.mean(stat_spectr_clunch, axis=0))
                            plt.show()
                            quit()
                    # uncomment the following lines to visualize 102nd sample or change num
                    # if num == 102:
                    #     print()
                    #     print(relax)
                    #     print(fingers)
                    #     stat = extract_spectr_statistics(sample_raw_eeg_data, sample_spectr - np.amin(sample_spectr))
                    #     for d in stat:
                    #         print('\t'.join(map(lambda x: "{:10.2f}".format(x), d)))
                    #         print()
                    #     plt.figure('statistics')
                    #     plt.plot(sample_freqs[0], np.mean(sample_spectr - np.amin(sample_spectr), axis=0))
                    #     plt.show()
                    #     quit()

                    if relax:
                        relax_samples.append(sample_spectr)
                        # plt.plot(sample_freqs[0], sample_spectr[0], color='red')
                    elif clunch:
                        clunch_samples.append(sample_spectr)

                    # plt.figure()
                    # plt.plot(sample_freqs[0], sample_spectr[0], color='blue')
                    # sample_freqs, sample_spectr = interface.get_spectr(sample_motor_data)
                    # plt.plot(sample_freqs[0], sample_spectr[0], color='green')
                    # plt.show()
                else:
                    sample_freqs, sample_spectr = interface.get_spectr(sample_motor_data)
                    if relax:
                        relax_samples.append(sample_spectr)
                        # plt.plot(sample_freqs[0], sample_spectr[0], color='red')
                    elif clunch:
                        clunch_samples.append(sample_spectr)
                        # plt.plot(sample_freqs[0], sample_spectr[0], color='black')

                    if SQUARE_MATRIX in modifiers:
                        for i in range(len(sample_spectr[0]) - len(sample_spectr)):
                            zeros_matrix = np.zeros((len(sample_spectr[0]),))
                            sample_spectr.append(zeros_matrix)
                sample_spectr = np.array(sample_spectr)
                if PADDING_1 in modifiers:
                    # sample_spectr_padding = np.pad(sample_spectr, (
                    # [(299 - sample_spectr.shape[0]) // 2, (299 - sample_spectr.shape[0]) // 2 + 1],
                    # [(299 - sample_spectr.shape[1]) // 2] * 2)).reshape(299, 299, 1)
                    # #add_zeros = np.zeros((299, 299, 2))
                    # sample_spectr_padding = np.concatenate((sample_spectr_padding,
                    #                                         sample_spectr_padding,
                    #                                         sample_spectr_padding), axis=2)
                    sample_spectr_padding = sample_spectr.reshape(*sample_spectr.shape, 1)
                    sample_spectr_padding = np.concatenate((sample_spectr_padding,
                                                            sample_spectr_padding,
                                                            sample_spectr_padding), axis=2)
                    sample_spectr_padding = cv2.resize(sample_spectr_padding, (299, 299))
                    if not any(fingers):
                        data.append(sample_spectr_padding)
                else:
                    data.append(sample_spectr)
                if RAW_EEG in modifiers:
                    if FILTER_PEAKS in modifiers:
                        filtered_raw_eeg_data = filtered_raw_eeg_data[:, :cut_raw_sample_num]
                        raw_eeg_data.append(filtered_raw_eeg_data)
                    else:
                        sample_raw_eeg_data = sample_raw_eeg_data[:, :cut_raw_sample_num]
                        raw_eeg_data.append(sample_raw_eeg_data)

                # plt.plot(sample_freqs[0], sample_spectr[0])
                if LABELS_STATE in modifiers:
                    labels_states.append([clunch, relax])
                if LABELS_FINGERS in modifiers:
                    labels_fingers.append(fingers)
                if SINGLE_LABEL in modifiers:
                    new_label = [0] * 10
                    for finger_id in range(len(fingers)):
                        if fingers[finger_id] == 1:
                            new_label[finger_id * 2 + int(relax)] = 1
                    single_labels.append(new_label)
                num += 1
                if num % 10 == 0:
                    print(num)

                # uncomment the following lines to visualize samples from debug arrays above

                # if num > 9:
                #     '''relax_samples = np.mean(np.array(relax_samples), axis=0)
                #     clunch_samples = np.mean(np.array(clunch_samples), axis=0)
                #     print(relax_samples.shape)
                #     for sensor_info in relax_samples:
                #         plt.plot(sample_freqs[0], sensor_info, color='black')
                #     for sensor_info in clunch_samples:
                #         plt.plot(sample_freqs[0], sensor_info, color='green')'''
                #     calm_eeg_data_spectr = interface.get_spectr(calm_eeg_data)[1][0]
                #     # plt.plot(sample_freqs[0], calm_eeg_data_spectr, color='red')
                #     # plt.show()
                #     print()
                #     # for index in range(len(relax_samples)):
                #     #     image_to_viz = np.concatenate((relax_samples[index], clunch_samples[index]), axis=0)
                #     #     #plt.imshow(relax_samples[index], cmap='hot')
                #     #     #plt.imshow(clunch_samples[index], cmap='hot')
                #     #     plt.imshow(image_to_viz, cmap='hot')
                #     #     plt.show()
                #     plt.figure('relax')
                #     image_to_viz = relax_samples[0]
                #     print('relax mean fc5 is', np.mean(relax_samples[0][2]))
                #     print('relax mean fc6 is', np.mean(relax_samples[0][3]))
                #     for da in relax_samples[1:]:
                #         image_to_viz = np.concatenate((image_to_viz, da[:4]), axis=0)
                #     plt.imshow(image_to_viz)
                #     print('relax mean is', np.mean(image_to_viz))
                #                 #     plt.figure('clunch')
                #     print('ckunch mean fc5 is', np.mean(clunch_samples[0][2]))
                #     print('ckunch mean fc6 is', np.mean(clunch_samples[0][3]))
                #     image_to_viz = clunch_samples[0]
                #     for da in clunch_samples[1:]:
                #         image_to_viz = np.concatenate((image_to_viz, da[:4]), axis=0)
                #     plt.imshow(image_to_viz)
                #     print('clunch mean is', np.mean(image_to_viz))
                #     plt.show()
                #     continue

        # list => np.ndarray
        data = np.array(data)
        labels_states = np.array(labels_states)
        labels_fingers = np.array(labels_fingers)
        raw_eeg_data = np.array(raw_eeg_data)
        single_labels = np.array(single_labels)
        if debug:
            [print(i.shape) for i in [data, labels_states, labels_fingers]]
        return num, data, labels_states, labels_fingers, raw_eeg_data, single_labels

    finally:
        interface.close_file()
        time_log_file.close()


# modifiers
RAW_EEG = 1
LABELS_STATE = 2
LABELS_FINGERS = 3
FILTER_PEAKS = 4
SQUARE_MATRIX = 5
SINGLE_LABEL = 6
PADDING_1 = 7

# sensors ids
INTERPOLATED_CHN = 2
AF_3 = 3
F_7 = 4
F_3 = 5
FC_5 = 6
T_7 = 7
P_7 = 8
O_1 = 9
O_2 = 10
P_8 = 11
T_8 = 12
FC_6 = 13
F_4 = 14
F_8 = 15
AF_4 = 16
RAW_CQ = 17
ALL_SENSORS = [AF_3, F_7, F_3, FC_5, T_7, P_7, O_1, O_2, P_8, T_8, FC_6, F_4, F_8, AF_4]
# ALL_SENSORS = [AF_3, AF_4, F_7, F_8, F_3, F_4, FC_5, FC_6, T_7, T_8, P_7, P_8, O_1, O_2]

plt.figure()
if __name__ == '__main__':
    # sensors = [F_7, F_8, AF_4, F_4, AF_3, F_3]
    frontal_sensors = []
    # motor_sensors = [F_7, F_8, FC_5, FC_6, F_3, F_4, AF_3, AF_4]
    motor_sensors = ALL_SENSORS
    raw_eeg_sensors = ALL_SENSORS
    modifiers = [LABELS_STATE, LABELS_FINGERS, SINGLE_LABEL, RAW_EEG, FILTER_PEAKS, PADDING_1]
    # list of csv dirs to read and save
    csv_data_directories = ['bogdan_comb_allhand']
    # 'bogdan_im_allhand']  # 'ilya_1_im']  # , 'Bogdan_1', 'denis1', 'denis1/save', 'fH13a',
    # '18071249', 'dW32o', 'kB18d', 'mK65k', 'oL43c',
    # 'dW32o', 'rU46w']
    # change csv_val_data_directory to the last dir in csv_data_directories lists
    # to see the possible validation array shape
    csv_val_data_directory = 'rU46w'
    save_data_directory = 'dataset'
    num = 0
    data, label_states, label_fingers, raw_eeg, single_labels = [], [], [], [], []
    for csv_dir in csv_data_directories:
        print(f'reading {csv_dir}')

        num, \
        new_data, new_label_states, \
        new_label_fingers, new_raw_eeg, \
        new_single_labels = proccess_protocol(csv_dir, frontal_sensors,
                                              motor_sensors, modifiers,
                                              debug=True, num=num,
                                              cut_raw_sample_num=250)
        # plt.show()
        # quit()
        print(f'saving {csv_dir}')
        # appending new data to resulting arrays
        print('appending new data')
        if new_data.any():
            for info_row in new_data:
                data.append(info_row)
        print('appanding done')
        if new_label_states.any():
            for info_row in new_label_states:
                label_states.append(info_row)
        if new_label_fingers.any():
            for info_row in new_label_fingers:
                label_fingers.append(info_row)
        if new_raw_eeg.any():
            for info_row in new_raw_eeg:
                raw_eeg.append(info_row)
        if new_single_labels.any():
            for info_row in new_single_labels:
                single_labels.append(info_row)
        if csv_dir == csv_val_data_directory:
            print(f'val data shape is {new_data.shape}')

    # printing stat info
    minm = np.amin(data)
    data -= minm
    data /= np.amax(data)
    print(data[data < 0.].shape)
    print('spectr min is', np.amin(data))
    print('spectr max is', np.amax(data))
    print('spectr mean is', np.mean(data))
    print()

    print('raw eeg min is', np.amin(raw_eeg))
    print('raw eeg max is', np.amax(raw_eeg))
    print('raw eeg mean is', np.mean(raw_eeg))

    raw_eeg -= np.amin(raw_eeg)
    raw_eeg /= np.amax(raw_eeg)
    # print(raw_eeg)
    print()
    print('raw eeg min is', np.amin(raw_eeg))
    print('raw eeg max is', np.amax(raw_eeg))
    print('raw eeg mean is', np.mean(raw_eeg))
    # check_data(data, single_labels, label_states, label_fingers, raw_eeg)
    print()
    print('start transforming')
    data = np.array(data)
    label_states = np.array(label_states)
    label_fingers = np.array(label_fingers)
    single_labels = np.array(single_labels)
    raw_eeg = np.array(raw_eeg)
    for i in [data, label_states, label_fingers, single_labels, raw_eeg]:
        print(i.shape)
    # plt.show()
    # saving data to files
    if not os.path.isdir(save_data_directory):
        os.mkdir(save_data_directory)
    with open(f'{save_data_directory}/data.pickle', mode='wb') as file:
        pickle.dump(data, file)
    if LABELS_STATE in modifiers:
        with open(f'{save_data_directory}/labels_states.pickle', mode='wb') as file:
            pickle.dump(label_states, file)
    if LABELS_FINGERS in modifiers:
        with open(f'{save_data_directory}/labels_fingers.pickle', mode='wb') as file:
            pickle.dump(label_fingers, file)
    if RAW_EEG in modifiers:
        with open(f'{save_data_directory}/raw_eeg_{len(frontal_sensors) + len(motor_sensors)}.pickle',
                  mode='wb') as file:
            pickle.dump(raw_eeg, file)
    if SINGLE_LABEL in modifiers:
        with open(f'{save_data_directory}/single_labels.pickle',
                  mode='wb') as file:
            pickle.dump(single_labels, file)
