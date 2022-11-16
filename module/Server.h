#ifndef _F_SERVER_H_
# define _F_SERVER_H_

# include <iostream>
# include <thread>
# include <map>
# include <unistd.h>
# include <netinet/in.h>
# include <sys/socket.h>
# include <sys/epoll.h>
# include <stdio.h>
# include <string.h>
# include <errno.h>
# include "Response.h"
# include "Request.h"
# include "protocol.h"

enum class Status
{
	WAITING,
	RUNNING,
	SHUTDOWN
};

class Server
{
public:
	Server ();
	~Server ();

	bool Init ();
	bool Listen (int port, int queue);
	void Wait (int queue);

	void Broadcast (char * buf, unsigned int length);

private:
	

private:
	Status status;
	
	int socketFd;
	struct sockaddr_in address;

	int epollFd;
	struct epoll_event *events;

	std::map<int, Response *> clients;
};

#endif
