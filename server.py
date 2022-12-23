from tensorflow import keras
from tensorflow.keras import layers
import ssl
import numpy as np
import time
from FLlib import FLModel, FLServer

# MNIST SSL certification
ssl._create_default_https_context = ssl._create_unverified_context

# model
class MNISTModel (FLModel):
	def __init__ (self):
		super ().__init__ ()

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

	def fit (self):
		batch_size = 128
		epochs = 1
		self.model.fit(self.x_train, self.y_train, batch_size=batch_size, epochs=epochs, validation_split=0.1)

	def evaluate (self):
		score = self.model.evaluate(self.x_test, self.y_test, verbose=0)
		print("Test loss:", score[0])
		print("Test accuracy:", score[1])

# FLServer - MNIST
class MNISTServer (FLServer):
	def load (self):
		super ().load ()
		# model
		self.model = MNISTModel ()
		self.model.load ()

	def federated_learning (self):
		epoch = 1
		participants = self.select_participants ()
		# can use parameters for custom signal
		parameters = [10, 9, 8, 7, 6, 5]
		# time
		transfer_start = time.time ()
		# FL
		self.collect_and_calculate_weights (epoch, participants, parameters)
		self.broadcast_weight ()
		# time
		transfer_end = time.time ()
		print ()
		print (f"total elapsed time: {transfer_end - transfer_start:.5f} sec")
		print ()

def main ():
	# port, max number of client connections
	server = MNISTServer (4242, 42)
	server.load ()
	server.until_client (int (input ("Enter the number of clients to use: ")))
	# loop
	while True:
		print ("Choose an action to execute")
		print ("1. Federeated Learning (FedAvg)")
		print ("2. Broadcast the weights")
		print ("3. Evaluate the model")
		print ("4. Exit")
		try:
			temp = input ("Please enter the number: ")
			select = int (temp)
		except:
			print ("Invalid Input:", temp)
			continue
		# case
		print ("")
		if select == 1:
			server.federated_learning ()
		if select == 2:
			server.broadcast_weight ()
		elif select == 3:
			server.model.evaluate ()
		elif select == 4:
			break

# entry
if __name__ == "__main__":
	main ()
