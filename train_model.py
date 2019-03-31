import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import time
from network.models import GanModel


def train(X, Y, epochs, batch_size, input_shape):

    # Return encoder, two decoders, and two discriminators
    model = GanModel(input_shape=input_shape, image_shape=(64, 64, 6))
    model.build_train_functions()

    errGA_sum = errGB_sum = errDA_sum = errDB_sum = 0
    display_iters = 1

    t0 = time.time()
    iters = X.shape[0] // batch_size
    # model.load_weights()
    for i in range(epochs):
        print("######################################################\n"
              "GLOBAL EPOCH --------------------------------------- {i}".format(i=i),
              "\n######################################################\n")

        # Train discriminators
        step = 0
        for iter in range(iters):
            errDA, errDB = model.train_discriminators(data_A=X[step:step + batch_size], data_B=Y[step:step + batch_size])
            step = step + batch_size
        errDA_sum += errDA[0]
        errDB_sum += errDB[0]

        # Train generators
        step = 0
        for iter in range(iters):
            errGA, errGB = model.train_generators(data_A=X[step:step + batch_size], data_B=Y[step:step + batch_size])
            step = step + batch_size
        errGA_sum += errGA[0]
        errGB_sum += errGB[0]

        # Visualization
        if i % display_iters == 0:

            print("----------")
            print('[iter %d] Loss_DA: %f Loss_DB: %f Loss_GA: %f Loss_GB: %f time: %f'
                  % (i, errDA_sum / display_iters, errDB_sum / display_iters,
                     errGA_sum / display_iters, errGB_sum / display_iters, time.time() - t0))
            print("----------")
            display_iters = display_iters + 1

        # Makes predictions after each epoch and save into temp folder.
        prediction = model.encoder.predict(X[0:2])
        prediction = model.dst_decoder.predict(prediction)
        cv.imwrite('data/models/temp/image{epoch}.jpg'.format(epoch=i + 0), prediction[0] * 255)

    model.save_weights()

    # Test model
    # prediction = encoder.predict(X[0:2])
    # prediction = dst_decoder.predict(prediction)

    # for i in range(1):
    #    plt.subplot(231), plt.imshow(X[i], 'gray')
    #    plt.subplot(232), plt.imshow(Y[i], 'gray')
    #    plt.subplot(233), plt.imshow(prediction[i], 'gray')
    #    plt.show()


def main():
    # Parameters
    epochs = 100
    batch_size = 5
    input_shape = (64, 64, 3)

    X = np.load('data/X.npy')
    Y = np.load('data/Y.npy')

    X = X.astype('float32')
    Y = Y.astype('float32')
    X /= 255
    Y /= 255

    # X = X[0:53]
    # Y = Y[0:53]

    train(X, Y, epochs, batch_size, input_shape)


if __name__ == "__main__":
    main()