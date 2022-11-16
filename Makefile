all		:
	@echo a

s:
	g++ -shared -fPIC module/Server.cpp module/Response.cpp module/Request.cpp -o libc_server.so
	python3 server.py

c:
	g++ -shared -fPIC module/Client.cpp -o libc_client.so
	python3 client.py

clean	:
	@rm libc_client.so libc_server.so
