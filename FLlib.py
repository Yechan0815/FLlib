from enum import Enum
import json
import ctypes
import numpy as np
import time

class TCode (Enum): 
	SYN = 0
	ACK = 1
	Select = 2
	Ignore = 3
	Unicast = 4
	Broadcast = 5
	Terminate = 6

# bridge
class ServerBridge:
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

		self.server_free_weight_json = module.server_free_weight_json
		self.server_free_weight_json.argtypes = (ctypes.POINTER (ctypes.c_wchar_p), ctypes.c_int)
		self.server_free_weight_json.restype = None

		self.server_destroy = module.server_destroy
		self.server_destroy.argtypes = None
		self.server_destroy.restype = None

class ClientBridge:
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

		self.client_free_weight_json = module.client_free_weight_json
		self.client_free_weight_json.argtypes = (ctypes.c_wchar_p, )
		self.client_free_weight_json.restype = None

		self.client_destroy = module.client_destroy
		self.client_destroy.argtypes = None
		self.client_destroy.restype = None

# server
class FLServer:
	def __init__ (self, port, max_client):
		self.port = port
		self.max_client = max_client
		# resource
		self.bridge = ServerBridge ("./libc_server.so")
		# FL
		self.total = -1
	
	def __del__ (self):
		self.bridge.server_destroy ()

	def load (self):	
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

	# default => FedAvg
	def combination_method (self, weights, participants_length):
		avg = weights[0]
		for index in range (1, participants_length):
			avg += weights[index]
		return avg / participants_length

	# default => all
	def select_participants (self):
		participants = []
		for i in range (0, self.total):
			participants.append (i)
		return participants

	def collect_and_calculate_weights (self, epoch, participants, parameters):
		# array to store a result weights
		weights_average = []
		# set
		weights_size = len (self.model.get_weights ())
		weights_offset = 0
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
			weights_average.append (self.combination_method (numpy_weight, participants_length))
			# free
			self.bridge.server_free_weight_json (weights_json, participants_length)	
			# next
			weights_offset += 1
			print ("Receiving weights from client {}/{}".format (weights_offset, weights_size))

		# update the model of server
		self.model.set_weights (weights_average)

	def broadcast_weight (self):
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

	# default => epoch: 1, participants: all
	def federated_learning (self):
		epoch = 1
		participants = self.select_participants ()
		parameters = []
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

# client
class FLClient:
	def __init__ (self):
		self.total = -1
		self.index = -1
		self.host = ""
		self.port = -1
		# resource
		self.bridge = ClientBridge ("./libc_client.so")

	def __del__ (self):
		self.bridge.client_destroy ()

	def load (self):
		print (end='')
		# implement

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

		# hand over
		self.depend_on_server ()
	
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

		# time
		transfer_start = time.time ()
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
		transfer_end = time.time ()
		print ()
		print (f"elapsed time for sending: {transfer_end - transfer_start:.5f} sec")

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

	def update_model (self):
		weights_size = len (self.model.get_weights ())
		weights_offset = 0

		# time
		transfer_start = time.time ()
		# receive
		weights = []
		# receive weights from server
		while weights_offset != weights_size:
			weights_json = self.bridge.client_receive_weight_json ()
			weights.append (np.array (json.loads (weights_json)))
			# next
			weights_offset += 1
			print ("Receiving weights from server {}/{}".format (weights_offset, weights_size))
		# update
		self.model.set_weights (weights)
		# time
		transfer_end = time.time ()
		print ()
		print (f"elapsed time for receiving: {transfer_end - transfer_start:.5f} sec")

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

# model
class FLModel:
	def __init__(self):
		self.index = -1
		self.model = None
		
	def get_weights (self):
		return self.model.get_weights ()
	
	def set_weights (self, weights):
		self.model.set_weights (weights)
