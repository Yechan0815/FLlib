import ctypes
import platform

path = "./libc_server.so"
c_module = ctypes.cdll.LoadLibrary(path)

serv = c_module.server_init
serv.restype = ctypes.c_bool

if serv():
	print ('running')
else:
	print ('failed to start server')
	
serv = c_module.server_listen
serv.argtypes = (ctypes.c_int, ctypes.c_int)
serv.restype = ctypes.c_bool

if serv(4242, 10):
	print ('listening')
else:
	print ('failed to listen')
	
serv = c_module.server_wait
serv.argtypes = (ctypes.c_int, )
serv.restype = None

serv(10);

print ('done')
