from enum import Enum
import ctypes
import ssl
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers

# MNIST SSL certification
ssl._create_default_https_context = ssl._create_unverified_context

class TCode (Enum): 
	SYN = 0
	ACK = 1
	Select = 2
	Ignore = 3
	Unicast = 4
	Broadcast = 5
	Terminate = 6

# bridge
class Bridge:
	def __init__ (self, path):
		module = ctypes.cdll.LoadLibrary(path)

		self.server_init = module.server_init
		self.server_init.argtypes = None
		self.server_init.restype = ctypes.c_bool

		self.server_listen = module.server_listen
		self.server_listen.argtypes = (ctypes.c_int, ctypes.c_int)
		self.server_listen.restype = ctypes.c_bool

		self.server_wait = module.server_wait
		self.server_wait.argtypes = (ctypes.c_int, )
		self.server_wait.restype = None

		self.server_destroy = module.server_destroy
		self.server_destroy.argtypes = None
		self.server_destroy.restype = None

# model
class ServerModel:
	def __init__ (self):
		self.index = -1

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
	
	def get_weights (self):
		return self.model.get_weights ()

	def fit (self):
		batch_size = 128
		epochs = 1
		self.model.fit(self.x_train, self.y_train, batch_size=batch_size, epochs=epochs, validation_split=0.1)

	def evaluate (self):
		score = self.model.evaluate(self.x_test, self.y_test, verbose=0)
		print("Test loss:", score[0])
		print("Test accuracy:", score[1])

class Server:
	def __init__ (self, port, max_client):
		self.port = port
		self.max_client = max_client
		# resource
		self.model = ServerModel ()
		self.bridge = Bridge ("./libc_server.so")

	def load (self):
		# model
		self.model.load ()
		# socket
		if not self.bridge.server_init ():
			raise Exception("Failed to initialize socket resource")
		if not self.bridge.server_listen (self.port, self.max_client):
			raise Exception("Failed to start server")
		print ("Started the server")

	def until_client (self, queue):
		print ("Waiting for clients...")
		self.bridge.server_wait (queue)
		print ("A total of {} clients connected".format (queue))

	def run (self):
		while True:
			print ("")
			print ("Choose an action to execute")
			print ("1. Federeated Learning (FedAvg)")
			print ("2. Evaluate the model")
			print ("4. Exit")
			select = int (input ("Please enter the number: "))
			if (select == 1):
				print ("Federated")
			elif (select == 2):
				print ("evaluate")
			elif (select == 4):
				break
			else:
				print ("Invalid input")

	def destroy (self):
		self.bridge.server_destroy ()

# entry
server = Server (4242, 42)
server.load ()
server.until_client (int (input ("Enter the number of clients to use: ")))
server.run ()
server.destroy ()
