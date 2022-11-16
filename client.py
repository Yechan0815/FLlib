from enum import Enum
import ssl
import ctypes
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

		self.client_init = module.client_init;
		self.client_init.argtypes = None
		self.client_init.restype = ctypes.c_bool

		self.client_connect = module.client_connect;
		self.client_connect.argtypes = (ctypes.c_wchar_p, ctypes.c_int)
		self.client_connect.restype = ctypes.c_bool

		self.client_handshake = module.client_handshake;
		self.client_handshake.argtypes = (ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
		self.client_handshake.restype = None 

		self.client_signal = module.client_signal;
		self.client_signal.argtypes = None
		self.client_signal.restype = ctypes.c_int

# model
class ClientModel:
	def __init__ (self):
		self.total = -1
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
		epochs = 1
		batch_size = 128
		self.model.fit(self.x_train, self.y_train, batch_size=batch_size, epochs=epochs, validation_split=0.1)

	def evaluate (self):
		score = self.model.evaluate(self.x_test, self.y_test, verbose=0)
		print("Test loss:", score[0])
		print("Test accuracy:", score[1])

class Client:
	def __init__ (self, host, port):
		self.total = -1
		self.index = -1
		self.host = host
		self.port = port
		# resource
		self.model = ClientModel ()
		self.bridge = Bridge ("./libc_client.so")

	def load (self):
		# model
		self.model.load ()
		# socket
		if not self.bridge.client_init ():
			raise Exception('Failed to initialize socket resource')
		if not self.bridge.client_connect (self.host, self.port):
			raise Exception('Failed to connect to server')
		print ("Connect to server successfully")
		# handshake
		out_total = ctypes.c_int ()
		out_index = ctypes.c_int ()
		self.bridge.client_handshake (out_total, out_index)
		if out_total.value < 0:
			raise Exception('Failed to handshaek')
		self.total = out_total.value
		self.index = out_index.value
		self.model.total = self.total
		self.model.index = self.index
		print ("Successful handshake with server: Assigned client index: {}/0-{}".format(self.index, self.total - 1))

	def run (self):
		while True:
			signal = self.bridge.client_signal ()
			if signal == TCode.Select.value:
				self.model.fit ()
			elif signal == TCode.Ignore.value:
				print ("ignore")
			elif signal == TCode.Terminate.value:
				break

	def destroy (self):
		print ("destroy")
			
"""
import json

js = json.dumps (model.get_weights()[0].tolist())
print (js)
	"""
client = Client ("127.0.0.1", 4242)
client.load ()
client.run ()
client.destroy ()