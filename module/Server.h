#ifndef _SERVER_H_
# define _SERVER_H_

# include <thread>
# include <unistd.h>
# include <netinet/in.h>
# include <sys/socket.h>
# include <sys/epoll.h>
# include <stdio.h>
# include <string.h>
# include <errno.h>

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

private:
	

private:
	Status status;
	
	int socketFd;
	struct sockaddr_in address;

	int epollFd;
	struct epoll_event *events;
};

#endif
