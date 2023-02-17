from tensorflow import keras
from tensorflow.keras import layers
import ssl
import numpy as np
from FLlib import FLModel, FLClient

# MNIST SSL certification
ssl._create_default_https_context = ssl._create_unverified_context

# model
class MNISTModel (FLModel):
	def __init__ (self):
		self.total = 1
		self.index = 0

	def load (self):
		num_classes = 10
		input_shape = (28, 28, 1)

		(x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()

		x_train = x_train.astype("float32") / 255
		x_test = x_test.astype("float32") / 255
		x_train = np.expand_dims(x_train, -1)
		x_test = np.expand_dims(x_test, -1)
		print("x_train shape:", x_train.shape)
		print(x_train.shape[0], "train samples")
		print(x_test.shape[0], "test samples")

		y_train = keras.utils.to_categorical(y_train, num_classes)
		y_test = keras.utils.to_categorical(y_test, num_classes)

		model = keras.Sequential(
			[
				keras.Input(shape=input_shape),
				layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
				layers.MaxPooling2D(pool_size=(2, 2)),
				layers.Conv2D(64, kernel_size=(3, 3), activation="relu"),
				layers.MaxPooling2D(pool_size=(2, 2)),
				layers.Flatten(),
				layers.Dropout(0.5),
				layers.Dense(num_classes, activation="softmax"),
			]
		)
		model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
		# property
		self.x_train = x_train
		self.y_train = y_train
		self.x_test = x_test
		self.y_test = y_test
		self.model = model

	def fit (self, epochs, parameters):
		batch_size = 128

		train_size = int (len (self.x_train) / self.total)

		print ("Dataset {}-{}/{}".format (train_size * self.index, train_size * (self.index + 1), len (self.x_train)))
		self.model.fit(
			self.x_train[train_size * self.index:train_size * (self.index + 1)],
			self.y_train[train_size * self.index:train_size * (self.index + 1)],
			batch_size=batch_size,
			epochs=epochs,
			validation_split=0.2
		)

	def evaluate (self):
		score = self.model.evaluate(self.x_test, self.y_test, verbose=0)
		print("Test loss:", score[0])
		print("Test accuracy:", score[1])

class MNISTClient (FLClient):
	def load (self):
		super ().load ()
		# model
		self.model = MNISTModel ()
		self.model.load ()

def main ():
    client = MNISTClient ()
    client.load ()
    while True:
        print ("")
        print ("Choose an action to execute")
        print ("1. Connect (client's flow is controlled by the server)")
        print ("2. Learning")
        print ("3. Evaluate the model")
        print ("4. Exit")
        try:
            temp = input ("Please enter the number: ")
            select = int (temp)
        except:
            print ("Invalid Input:", temp)
            continue
        # case
        if select == 1:
            try:
                host = input ("host: ")
                port = int (input ("port: "))
                client.connect (host, port)
            except:
                print ("Failed to connect to server")
        elif select == 2:
            client.model.fit (int (input ("Enter the epoch to use: ")))
        elif select == 3:
            client.model.evaluate ()
        elif select == 4:
            break

if __name__ == "__main__":
    main ()
