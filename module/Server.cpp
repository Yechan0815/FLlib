#include "Server.h"

static Server * server = nullptr;

/* coplien form */
Server::Server ()
{
	status = Status::WAITING;
	/* map */
	clients.clear();
}

Server::~Server ()
{
	char buf[2] = { (char) TCode::Terminate, 0 };
	/* send close signal to clients */
	Broadcast (buf, 1);
	/* close */
	for (std::map<int, Response *>::iterator it = clients.begin (); it != clients.end (); ++it)
	{
		::close (it->first);
		delete it->second;
	}
	::close (socketFd);
	delete[] events;
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
		return false;
	
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
	char handshake[13] = { (char) TCode::SYN, 0, };	
	char buf[16];
	struct epoll_event event;
	struct sockaddr_in caddr;
	socklen_t clen;
	int clientFd;
	int ready;
	unsigned int bytes;
	int conn;

	conn = 0;
	while (1)
	{
		ready = epoll_wait (epollFd, events, queue, -1);
		if (ready < 0)
			throw std::runtime_error ("Server module: epoll_wait: 65 line");

		for (int i = 0; i < ready; ++i)
		{
			if (events[i].data.fd == socketFd)
			{
				clen = sizeof (caddr);
				clientFd = accept (socketFd, (struct sockaddr *) &caddr, &clen);
				if (clientFd < 0)
					throw std::runtime_error ("Server module: accept: 73 line");
				/* handshake */
				*((unsigned int *)(handshake + 1)) = 8;
				*((int *)(handshake + 5)) = queue;
				*((int *)(handshake + 9)) = clients.size();
				::write (clientFd, handshake, 13);
				/* new client */
				clients.insert (std::pair<int, Response *>(clientFd, new Response));
				clients[clientFd]->SetIndex (clients.size() - 1);
				/* add epoll */
				event.events = EPOLLIN;
                event.data.fd = clientFd;
				if (epoll_ctl (epollFd, EPOLL_CTL_ADD, clientFd, &event) < 0)
					throw std::runtime_error ("Server module: epoll_ctl: 93 line");
				continue;
            }
			/* client */
			if (events[i].events & EPOLLIN)
			{
				buf[0] = -1;
				bytes = ::read (events[i].data.fd, buf, 1);
				if (bytes < 0)
					throw std::runtime_error ("Server module: read: 99 line");
				if (bytes == 0)
					throw std::runtime_error ("Server module: disconnected with client");
				if (buf[0] == (char) TCode::ACK)
				{
					std::cout << "handshake with client index " << clients[events[i].data.fd]->GetIndex () << std::endl;
					event.data.fd = events[i].data.fd;
					if (epoll_ctl (epollFd, EPOLL_CTL_DEL, event.data.fd, &event) < 0)
						throw std::runtime_error ("Server module: epoll_ctl: 119 line");
					++conn;
				}
				else
					throw std::runtime_error ("Server Module: client performed an undefined action during the handshake");
			}
		}
		if (conn == queue)
			break;
	}
}

void Server::Broadcast (char * buf, unsigned int length)
{
	struct epoll_event event;
	std::map<int, Request> requests;
	unsigned int bytes;
	int ready;

	for (std::map<int, Response *>::iterator it = clients.begin (); it != clients.end (); ++it)
	{
		/* add epoll */
		event.events = EPOLLOUT;
		event.data.fd = it->first;
		if (epoll_ctl (epollFd, EPOLL_CTL_ADD, it->first, &event) < 0)
			throw std::runtime_error ("Server module: epoll_ctl: 141 line");
		requests.insert (std::pair<int, Request>(it->first, Request ()));
		requests[it->first].length = length;
		requests[it->first].offset = 0;
	}

	while (1)
	{
		ready = epoll_wait (epollFd, events, requests.size(), -1);
		if (ready < 0)
			throw std::runtime_error ("Server module: epoll_wait: 149 line");

		for (int i = 0; i < ready; ++i)
		{
			if (events[i].events & EPOLLOUT)
			{
				bytes = ::write (events[i].data.fd, buf + requests[events[i].data.fd].offset,
						length - requests[events[i].data.fd].offset);
				requests[events[i].data.fd].offset += bytes;
				if (requests[events[i].data.fd].offset == length)
				{
					event.data.fd = events[i].data.fd;
					if (epoll_ctl (epollFd, EPOLL_CTL_DEL, events[i].data.fd, &event) < 0)
						throw std::runtime_error ("Server module: epoll_ctl: 166 line");
					requests.erase (events[i].data.fd);
				}
			}
		}
		if (requests.size() == 0)
			break;
	}
}

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
		if (server)
			delete server;
	}

	wchar_t* serv()
	{
		return L"test";
	}
}
