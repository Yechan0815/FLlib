from enum import Enum
import json
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

		self.server_FL_start = module.server_FL_start
		self.server_FL_start.argtypes = (ctypes.c_int, ctypes.POINTER (ctypes.c_int), ctypes.c_int)
		self.server_FL_start.restype = None

		self.server_FL_receive_weight_json = module.server_FL_receive_weight_json
		self.server_FL_receive_weight_json.argtypes = None
		self.server_FL_receive_weight_json.restype = ctypes.POINTER (ctypes.c_wchar_p)

		self.server_FL_send_weight_json = module.server_FL_send_weight_json
		self.server_FL_send_weight_json.argtypes = (ctypes.c_wchar_p, )
		self.server_FL_send_weight_json.restype = None 

		self.server_FL_update_model = module.server_FL_update_model
		self.server_FL_update_model.argtypes = None
		self.server_FL_update_model.restype = None

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
	
	def set_weights (self, weights):
		self.model.set_weights (weights)

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
		# FL
		self.total = -1
		self.weights_average = []

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
		self.total = queue

	def select_clients (self):
		participants = []
		for i in range (0, self.total):
			participants.append (i)
		return participants
	
	def combination_method (self, weights, participants_length):
		avg = weights[0]
		for index in range (1, participants_length):
			avg += weights[index]
		return avg / participants_length

	def federated_learning (self):
		# array to store a result weights
		self.weights_average = []
		# set
		epoch = int (input ("Enter the epoch to use: "))
		weights_size = len (self.model.get_weights ())
		weights_offset = 0
		participants = self.select_clients ()
		participants_length = len (participants)

		# Federated Learning
		participants = (ctypes.c_int * len (participants)) (*participants)
		self.bridge.server_FL_start (epoch, participants, participants_length)
		# Receive weights of all clients that has been selected in this round
		while weights_offset != weights_size:
			weights_json = self.bridge.server_FL_receive_weight_json ()
			# calculate the average
			numpy_weight = []
			for i in range (0, participants_length):
				numpy_weight.append (np.array (json.loads (weights_json[i])))
			self.weights_average.append (self.combination_method (numpy_weight, participants_length))
			# next
			weights_offset += 1
			print ("Receiving weights from client {}/{}".format (weights_offset, weights_size))

		# update the model of server
		self.model.set_weights (self.weights_average)

	def broadcast_model (self):
		self.bridge.server_FL_update_model ()
		# update the model of client
		weights_size = len (self.model.get_weights ())
		weights_offset = 0	
		# broadcast the weights of model
		while weights_offset != weights_size:
			weights_json = json.dumps (self.model.get_weights ()[weights_offset].tolist())
			self.bridge.server_FL_send_weight_json (weights_json)
			# next
			weights_offset += 1
			print ("Sending weights to client {}/{}".format (weights_offset, weights_size))

	def run (self):
		while True:
			print ("")
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
				self.federated_learning ()
				self.broadcast_model ()
			if select == 2:
				self.broadcast_model ()
			elif select == 3:
				self.model.evaluate ()
			elif select == 4:
				break

	def destroy (self):
		self.bridge.server_destroy ()

# entry
server = Server (4242, 42)
server.load ()
server.until_client (int (input ("Enter the number of clients to use: ")))
server.run ()
server.destroy ()
