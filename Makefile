all		:
	@echo a

s:
	g++ -shared -fPIC module/Server.cpp module/Response.cpp -o libc_server.so
	python3 server.py

c:
	g++ -shared -fPIC module/Client.cpp -o libc_client.so
	python3 client.py
