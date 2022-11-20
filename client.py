from enum import Enum
import json
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

		self.client_init = module.client_init
		self.client_init.argtypes = None
		self.client_init.restype = ctypes.c_bool

		self.client_connect = module.client_connect
		self.client_connect.argtypes = (ctypes.c_wchar_p, ctypes.c_int)
		self.client_connect.restype = ctypes.c_bool

		self.client_handshake = module.client_handshake
		self.client_handshake.argtypes = (ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
		self.client_handshake.restype = None 

		self.client_signal = module.client_signal
		self.client_signal.argtypes = None
		self.client_signal.restype = ctypes.c_int

		self.client_get_fl_data = module.client_get_fl_data
		self.client_get_fl_data.argtypes = (
				ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
		)
		self.client_get_fl_data.restype = None

		self.client_send_weight_json = module.client_send_weight_json
		self.client_send_weight_json.argtypes = (ctypes.c_wchar_p, )
		self.client_send_weight_json.restype = ctypes.c_bool

		self.client_receive_weight_json = module.client_receive_weight_json
		self.client_receive_weight_json.argtypes = None 
		self.client_receive_weight_json.restype = ctypes.c_wchar_p

		self.client_destroy = module.client_destroy
		self.client_destroy.argtypes = None
		self.client_destroy.restype = None

# model
class ClientModel:
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
	
	def get_weights (self):
		return self.model.get_weights ()

	def set_weights (self, weights):
		self.model.set_weights (weights)

	def fit (self, epochs):
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

class Client:
	def __init__ (self):
		self.total = -1
		self.index = -1
		self.host = ""
		self.port = -1
		# resource
		self.model = ClientModel ()
		self.bridge = Bridge ("./libc_client.so")

	def load (self):
		# model
		self.model.load ()

	def connect (self, host, port):
		self.host = host
		self.port = port
		# socket
		if not self.bridge.client_init ():
			raise Exception('Failed to initialize socket resource')
		if not self.bridge.client_connect (self.host, self.port):
			raise Exception('Failed to connect to server')
		print ("\nConnect to server successfully")
		print ("> host: {}".format (self.host))
		print ("> port: {}".format (self.port))

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
	
	def select (self):
		# get requirements
		out_participants_select = ctypes.c_int ()
		out_participants_ignore = ctypes.c_int ()
		out_epoch = ctypes.c_int ()
		self.bridge.client_get_fl_data (out_participants_select, out_participants_ignore, out_epoch)

		print ("Client index {} was selected for this round of federated learning".format (self.index))
		print ("> Total number of clients: {}".format (self.total))
		print ("> Number of Participants: {}".format (out_participants_select.value))
		print ("> Number of Non-participants: {}".format (out_participants_ignore.value))
		print ("> Client Index: {}".format (self.index))
		print ("> Required Epoch: {}".format (out_epoch.value))

		# Learning
		self.model.fit (out_epoch.value)

		# Send weights of the model of this client
		weights_size = len (self.model.get_weights ())
		weights_offset = 0
		# Send
		while weights_offset != weights_size:
			weights_json = json.dumps (self.model.get_weights ()[weights_offset].tolist())
			self.bridge.client_send_weight_json (weights_json)
			# next
			weights_offset += 1
			print ("Sending weights to server {}/{}".format (weights_offset, weights_size))

	def update_model (self):
		weights_size = len (self.model.get_weights ())
		weights_offset = 0

		weights = []
		# Receive weights from server
		while weights_offset != weights_size:
			weights_json = self.bridge.client_receive_weight_json ()
			weights.append (np.array (json.loads (weights_json)))
			# next
			weights_offset += 1
			print ("Receiving weights from server {}/{}".format (weights_offset, weights_size))
		# update
		self.model.set_weights (weights)

	def ignore (self):
		# get requirements
		out_participants_select = ctypes.c_int ()
		out_participants_ignore = ctypes.c_int ()
		self.bridge.client_get_fl_data (out_participants_select, out_participants_ignore, None)

		print ("Client index {} was not selected for this round of federated learning".format (self.index))
		print ("> Total number of clients: {}".format (self.total))
		print ("> Number of Participants: {}".format (out_participants_select.value))
		print ("> Number of Non-participants: {}".format (out_participants_ignore.value))
		print ("> Client Index: {}".format (self.index))

	def depend_on_server (self):
		while True:
			print ("")
			print ("Controlled by server...")
			signal = self.bridge.client_signal ()
			if signal == TCode.Select.value:
				self.select ()	
			elif signal == TCode.Ignore.value:
				self.ignore ()
			elif signal == TCode.Broadcast.value:
				self.update_model ()
			elif signal == TCode.Terminate.value:
				print ("Close signal was broadcasted from server")
				break
	
	def run (self):
		while True:
			print ("")
			print ("Choose an action to execute")
			print ("1. Connect (flow control of client is done by the server)")
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
					self.connect (host, port)
					self.depend_on_server ()
				except:
					print ("Failed to connect to server")
			elif select == 2:
				self.model.fit (int (input ("Enter the epoch to use: ")))
			elif select == 3:
				self.model.evaluate ()
			elif select == 4:
				break

	def destroy (self):
		self.bridge.client_destroy ()
			
client = Client ()
client.load ()
client.run ()
client.destroy ()
