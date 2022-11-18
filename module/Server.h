#ifndef _F_SERVER_H_
# define _F_SERVER_H_

# include <locale>
# include <codecvt>
# include <algorithm>
# include <iostream>
# include <thread>
# include <map>
# include <vector>
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

	void FLStart (int epoch, int * participants, int number);
	wchar_t ** FLReceiveWeight ();

	void Broadcast (const char * buf, unsigned int length);
	void BroadcastTo (char * buf, unsigned int length, int * participants, int number);

private:
	

private:
	Status status;
	
	int socketFd;
	struct sockaddr_in address;

	int epollFd;
	struct epoll_event *events;

	std::map<int, Response *> clients;
	std::vector<int> selectedIndex;
};

#endif
