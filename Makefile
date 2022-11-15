all		:
	g++ -shared -fPIC module/Server.cpp module/Response.cpp -o libc_server.so
	python3 load.py
