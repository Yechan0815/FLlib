all		:
	g++ -shared -fPIC module/Server.cpp -o libc_server.so
	python3 load.py
