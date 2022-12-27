CC			= g++
RM			= rm -rf

SERVER_SRCS	= module/Server.cpp module/Response.cpp module/Request.cpp
CLIENT_SRCS	= module/Client.cpp

SERVER_OBJS	= $(patsubst %.cpp,%.o,$(SERVER_SRCS))
CLIENT_OBJS	= $(patsubst %.cpp,%.o,$(CLIENT_SRCS))

SERVER_MODULE = module/libc_server.so
CLIENT_MODULE = module/libc_client.so

all: $(SERVER_MODULE) $(CLIENT_MODULE)

%.o: %.cpp
	$(CC) -fPIC -c $< -o $@

$(SERVER_MODULE): $(SERVER_OBJS)
	$(CC) -shared $(SERVER_OBJS) -o $(SERVER_MODULE)

$(CLIENT_MODULE): $(CLIENT_OBJS)
	$(CC) -shared $(CLIENT_OBJS) -o $(CLIENT_MODULE)

re: fclean all

clean:
	$(RM) $(SERVER_OBJS) $(CLIENT_OBJS)

fclean: clean
	$(RM) $(SERVER_MODULE) $(CLIENT_MODULE)

