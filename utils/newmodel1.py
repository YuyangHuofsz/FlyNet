#This file aims to try 3 channels input
#To use consecutive images as RGB channels

from PIL import Image
import numpy as np
import os
from glob import glob

from keras.models import Model
from keras.layers import Input, concatenate, Conv2D, MaxPooling2D, Conv2DTranspose
from keras.optimizers import Adam
from keras import backend as K
from keras.callbacks import ModelCheckpoint, EarlyStopping
from random import shuffle


#no cv2
#no skimage

class DataGenerator:
    def __init__(self, dim_x = 128, dim_y = 128, dim_z = 0, batch_size = 32, shuffle = True, directory = "./nTrain"):
        #Initialization
        self.dim_x = dim_x
        self.dim_y = dim_y
        self.dim_z = dim_z
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.directory = directory


    def dataGenerate3Channels(self, directory):
        while 1:
            print("!!!!!Now Starts with a new round!!!!!")
            folders = sorted(glob(directory + "/*/*/"))
            shuffle(folders)            

            for i in folders:               

                #print(i)
                fileo = sorted(glob(i+'*[0-9].png'))
                filem = sorted(glob(i+'*mask.png'))
                #print(len(fileo))
                #print(len(filem))
                for j in range(len(fileo) - 2):
                    train = []
                    y = []


                    img = Image.open(fileo[j])
                    resized = np.asarray(img.resize((128, 128)))
                    train.append(resized)

                    img2 = Image.open(fileo[j+1])
                    resized = np.asarray(img2.resize((128, 128)))
                    train.append(resized)

                    img3 = Image.open(fileo[j+2])
                    resized = np.asarray(img3.resize((128, 128)))
                    train.append(resized)

                    train = np.asarray(train)
                    train = np.moveaxis(train, 0, -1)
                    train = train[np.newaxis,...]

                    



                    imgy = Image.open(filem[j])
                    resizedy = np.asarray(imgy.resize((128, 128)))
                    if(resizedy.max() == 255):
                        resizedy = resizedy / 255
                    y.append(resizedy)
                    '''

                    imgy2 = Image.open(filem[j+1])
                    resizedy = np.asarray(imgy2.resize((128, 128)))
                    if(resizedy.max() == 255):
                        resizedy = resizedy / 255
                    y.append(resizedy)

                    imgy3 = Image.open(filem[j+2])
                    resizedy = np.asarray(imgy3.resize((128, 128)))
                    if(resizedy.max() == 255):
                        resizedy = resizedy / 255
                    y.append(resizedy)
                    '''

                    y = np.asarray(y)
                    #y = np.moveaxis(y, 0, -1)
                    y = y[...,np.newaxis]


                    yield (train, y)


    


class Parameters:
    directory = "./"
    directory2 = "./AD"
    trainstartEP = 31
    trainendEP = 33
    #One good pick: 25-26
    teststartEP = 31
    testendEP = 32
    valEP =[]
    trainstartLA = 47
    trainendLA = 52
    teststartLA = 50
    testendLA = 51
    valLA =[]
    trainstartAD = -12
    trainendAD = -10
    teststartAD = -11
    testendAD = -10
    valAD =[]

    #y direction um/pixel
    yfactor = 1.12 * 200 / 128
    #x direction um/pixel
    xfactor = 2.2
    #time frames/second
    timefactor = 129.9

    valifolder = 8
    testfolder = 9



def dice_coef(y_true, y_pred):
    smooth = 1.
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)
def dice_coef_loss(y_true, y_pred):
    return -dice_coef(y_true, y_pred)

def get_model():
    inputs = Input((128,128, 3))
    conv1 = Conv2D(32, (3, 3), activation='relu', padding='same')(inputs)
    conv1 = Conv2D(32, (3, 3), activation='relu', padding='same')(conv1)
    pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

    conv2 = Conv2D(64, (3, 3), activation='relu', padding='same')(pool1)
    conv2 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv2)
    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

    conv3 = Conv2D(128, (3, 3), activation='relu', padding='same')(pool2)
    conv3 = Conv2D(128, (3, 3), activation='relu', padding='same')(conv3)
    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

    conv4 = Conv2D(256, (3, 3), activation='relu', padding='same')(pool3)
    conv4 = Conv2D(256, (3, 3), activation='relu', padding='same')(conv4)
    pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

    conv5 = Conv2D(512, (3, 3), activation='relu', padding='same')(pool4)
    conv5 = Conv2D(512, (3, 3), activation='relu', padding='same')(conv5)

    up6 = concatenate([Conv2DTranspose(256, (2, 2), strides=(2, 2), padding='same')(conv5), conv4], axis=3)
    conv6 = Conv2D(256, (3, 3), activation='relu', padding='same')(up6)
    conv6 = Conv2D(256, (3, 3), activation='relu', padding='same')(conv6)

    up7 = concatenate([Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same')(conv6), conv3], axis=3)
    conv7 = Conv2D(128, (3, 3), activation='relu', padding='same')(up7)
    conv7 = Conv2D(128, (3, 3), activation='relu', padding='same')(conv7)

    up8 = concatenate([Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(conv7), conv2], axis=3)
    conv8 = Conv2D(64, (3, 3), activation='relu', padding='same')(up8)
    conv8 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv8)

    up9 = concatenate([Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(conv8), conv1], axis=3)
    conv9 = Conv2D(32, (3, 3), activation='relu', padding='same')(up9)
    conv9 = Conv2D(32, (3, 3), activation='relu', padding='same')(conv9)

    conv10 = Conv2D(1, (1, 1), activation='sigmoid')(conv9)

    model = Model(inputs=[inputs], outputs=[conv10])
    #model.layers[2].trainable = False
    return model


if __name__ == '__main__':

    directory = "./nTrain"

    #get the data
    parameters = Parameters()
    #train, y, X_validate, y_validate, X_test, y_test = generateData()
    trainGenerator = DataGenerator().dataGenerate3Channels("./nTrain")
    X_validate = np.load("./X_validate.npy")
    y_validate = np.load("./y_validate.npy")
    X_validate=X_validate[...,np.newaxis]
    y_validate=y_validate[...,np.newaxis]

    #Set the model
    K.set_image_data_format('channels_last')
    model=get_model()
    model.compile(optimizer=Adam(lr=1e-5), loss=dice_coef_loss, metrics=[dice_coef])
    model_checkpoint = ModelCheckpoint(directory+'/weights_newchannel.h5', monitor='val_loss', save_best_only=True)
    earlystop = EarlyStopping(monitor='val_loss', patience=3, mode='auto')
    
    

    #Train
    #model.fit(train, y, batch_size=32, epochs=150, verbose=1, shuffle=True, callbacks=[model_checkpoint, earlystop],validation_data=(X_test, y_test))
    model.fit_generator(generator = trainGenerator, steps_per_epoch = 10000, epochs = 20, verbose = 1,
        #callbacks = [model_checkpoint, earlystop],
        #validation_data = (X_validate, y_validate)
        )

    #Test
    #a=model.predict(X_test, batch_size=32, verbose=2)