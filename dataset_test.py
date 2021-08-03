import pickle
import numpy as np
import matplotlib.pyplot as plt

plt.figure('dataset test')

with open('dataset/data.pickle', mode='rb') as file:
    data = pickle.load(file)
with open('dataset/labels_fingers.pickle', mode='rb') as file:
    labels_fingers = pickle.load(file)
with open('dataset/labels_states.pickle', mode='rb') as file:
    labels_states = pickle.load(file)

# print(data.shape)
# print(np.sum(labels_fingers, axis=0))
res_image = np.array(data[10])  # np.concatenate((data[0], data[1]), axis=0)
for i in range(11, 11):
    print(labels_states[i])
    # new_image = np.concatenate((data[i * 2], data[i * 2 + 1]), axis=0)
    # new_image = np.concatenate((data[i], data[i * 2 + 1]), axis=0)
    res_image = np.concatenate((res_image, data[i]), axis=1)
plt.imshow(res_image[:, :, 0], cmap='hot')
# print('spectr min is', np.amin(data))
# print('spectr max is', np.amax(data))
# print('spectr mean is', np.mean(data))

# print('sample minm is', np.amin(data[100, 2]))
# plt.plot(numpy.arange(data.shape[2]-4), data[0, 0][2:-2])
plt.figure()
res_image = np.array(data[10])  # np.concatenate((data[0], data[1]), axis=0)
for i in range(20, 25):
    print(labels_states[i])
    # new_image = np.concatenate((data[i * 2], data[i * 2 + 1]), axis=0)
    # new_image = np.concatenate((data[i], data[i * 2 + 1]), axis=0)
    res_image = np.concatenate((res_image, data[i]), axis=1)
plt.imshow(res_image[:, :, 0], cmap='hot')
print('spectr min is', np.amin(data))
print('spectr max is', np.amax(data))
print('spectr mean is', np.mean(data))

plt.show()

