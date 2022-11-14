#include <iostream>
#include <map> // socket:block
#include "Server.h"

static Server * server = nullptr;

/* coplien form */
Server::Server ()
{
	status = Status::WAITING;
}

Server::~Server ()
{
	std::cout << "destruct" << std::endl;
}

/* public */
bool Server::Init ()
{
	if ((socketFd = ::socket (AF_INET, SOCK_STREAM, 0)) == -1)
		return false;
	if ((epollFd = ::epoll_create (42)) == -1)
		return false;

	return true;
}

bool Server::Listen (int port, int queue)
{
	struct epoll_event event;
	
	address.sin_family = AF_INET;
	address.sin_port = htons(port);
	address.sin_addr.s_addr = htonl(INADDR_ANY);

	if (::bind (socketFd, (struct sockaddr *) &address, sizeof (address)) == -1)
	{
		std::cout << strerror(errno) << std::endl;
		return false;
	}
	
	if (::listen (socketFd, queue) == -1)
		return false;
	
	events = new struct epoll_event[queue + 1];
	bzero (events, (queue + 1) * sizeof(struct epoll_event));

	event.events = EPOLLIN;
	event.data.fd = socketFd;
	if (epoll_ctl (epollFd, EPOLL_CTL_ADD, socketFd, &event) < 0)
		return false;
	
	status = Status::RUNNING;
	return true;
}

void Server::Wait (int queue)
{
	struct sockaddr_in caddr;
	socklen_t clen;
	int clientFd;
	int ready;

	while (1)
	{
		ready = epoll_wait (epollFd, events, queue, -1);
		if (ready < 0)
			throw std::runtime_error ("Server module: epoll_wait: 61 line");

		for (int i = 0; i < ready; ++i)
		{
			if (events[i].data.fd == socketFd)
			{
				clientFd = accept (socketFd, (struct sockaddr *) &caddr, &clen);
				if (clientFd < 0)
					throw std::runtime_error ("Server module: accept: 71 line");
				::write (clientFd, "input? ", 7);
			}
		}
	}
}

/* export method */
extern "C"
{
	bool server_init ()
	{
		if (server != nullptr)
			return false;

		server = new Server;
		return server->Init ();
	}

	bool server_listen (int port, int queue)
	{
		return server->Listen (port, queue);
	}

	void server_wait (int queue)
	{
		server->Wait (queue);
	}

	void server_destroy ()
	{
		delete server;
	}

	wchar_t* serv()
	{
		return L"test";
	}
}
