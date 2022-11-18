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
	/* no longer accepting new clients */
	event.data.fd = socketFd;
	if (epoll_ctl (epollFd, EPOLL_CTL_DEL, socketFd, &event) < 0)
		throw std::runtime_error ("Server module: epoll_ctl: 133 line");
}

void Server::FLStart (int epoch, int * participants, int number)
{
	std::vector<int> target (participants, participants + number);
	std::vector<int> ignoredIndex;
	char buf[18] = { 0, };

	selectedIndex.clear ();
	/* split */
	for (unsigned int i = 0; i < clients.size (); ++i)
	{
		if (std::find (target.begin (), target.end (), i) == target.end ())
			ignoredIndex.push_back (i);
		else
			selectedIndex.push_back (i);
	}

	/* Code, Bytes, Selected participants, Ignored participants, Epoch */
	*buf = (char) TCode::Select;
	*((unsigned int *) (buf + 1)) = 12;
	*((int *) (buf + 5)) = static_cast<int> (selectedIndex.size ());
	*((int *) (buf + 9)) = static_cast<int> (ignoredIndex.size ());
	*((int *) (buf + 13)) = epoch;
	/* broadcast to selected clients */
	if (selectedIndex.size () != 0)
		BroadcastTo (buf, 17, &selectedIndex[0], static_cast<int> (selectedIndex.size ()));

	/* broadcast to ignored clients */
	*buf = (char) TCode::Ignore;
	*((unsigned int *) (buf + 1)) = 8;
	if (ignoredIndex.size () != 0)
		BroadcastTo (buf, 13, &ignoredIndex[0], static_cast<int> (ignoredIndex.size ()));
}

wchar_t ** Server::FLReceiveWeight ()
{
	Response *response;
	struct epoll_event event;
	unsigned int bytes;
	char buf[16];
	int ready;
	int count;
	/* result */
	wchar_t ** result;

	count = static_cast<int> (selectedIndex.size ());
	for (std::vector<int>::iterator idx = selectedIndex.begin (); idx != selectedIndex.end (); ++idx)
	{
		for (std::map<int, Response *>::iterator it = clients.begin (); it != clients.end (); ++it)
		{
			if (*idx == it->second->GetIndex ())
			{
				/* add epoll */
				event.events = EPOLLIN;
				event.data.fd = it->first;
				if (epoll_ctl (epollFd, EPOLL_CTL_ADD, it->first, &event) < 0)
					throw std::runtime_error ("Server module: epoll_ctl: 183 line");
				it->second->SetBHead (false);
				break;
			}
		}
	}

	while (count)
	{
		ready = epoll_wait (epollFd, events, selectedIndex.size (), -1);
		if (ready < 0)
			throw std::runtime_error ("Server module: epoll_wait: 194 line");

		for (int i = 0; i < ready; ++i)
		{
			if (events[i].events & EPOLLIN)
			{
				response = clients[events[i].data.fd];
				if (!response->GetBHead ())
				{
					/* code, bytes */
					bytes = ::read (events[i].data.fd, buf, 5);
					if (bytes < 0)
						throw std::runtime_error ("Server module: read: 205 line");
					if (bytes == 0)
						throw std::runtime_error ("Server module: disconnected with client");
					if (buf[0] != (char) TCode::Unicast)
						throw std::runtime_error ("Server Module: client performed an undefined action during weight sharing");
					response->Init (*((unsigned int *) (buf + 1)));
					response->SetSize (*((unsigned int *) (buf + 1)));
					response->SetBHead (true);
					continue;
				}
				/* body */
				bytes = ::read (
						events[i].data.fd, 
						response->GetBuffer () + response->GetOffset (),
						response->GetSize () - response->GetOffset ()
				);
				response->SetOffset (response->GetOffset () + bytes);
				if (response->GetOffset () == response->GetSize ())
				{
					event.data.fd = events[i].data.fd;
					if (epoll_ctl (epollFd, EPOLL_CTL_DEL, event.data.fd, &event) < 0)
						throw std::runtime_error ("Server module: epoll_ctl: 230 line");
					--count;
				}
			}
		}
	}

	/* Response To Array of wchat_t * */
	result = new wchar_t *[selectedIndex.size () + 1];
	count = 0;
	for (std::vector<int>::iterator idx = selectedIndex.begin (); idx != selectedIndex.end (); ++idx)
	{
		for (std::map<int, Response *>::iterator it = clients.begin (); it != clients.end (); ++it)
		{
			if (*idx == it->second->GetIndex ())
			{
				result[count] = new wchar_t[it->second->GetSize () + 2];
				mbstowcs (result[count], it->second->GetBuffer (), it->second->GetSize () + 1);
				++count;
				break;
			}
		}
	}
	result[count] = NULL;

	return result;
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
			throw std::runtime_error ("Server module: epoll_ctl: 176 line");
		requests.insert (std::pair<int, Request>(it->first, Request ()));
		requests[it->first].length = length;
		requests[it->first].offset = 0;
	}

	while (1)
	{
		ready = epoll_wait (epollFd, events, requests.size(), -1);
		if (ready < 0)
			throw std::runtime_error ("Server module: epoll_wait: 185 line");

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
						throw std::runtime_error ("Server module: epoll_ctl: 199 line");
					requests.erase (events[i].data.fd);
				}
			}
		}
		if (requests.size() == 0)
			break;
	}
}

void Server::BroadcastTo (char * buf, unsigned int length, int * participants, int number)
{
	struct epoll_event event;
	std::map<int, Request> requests;
	unsigned int bytes;
	int ready;
	std::vector<int> target (participants, participants + number);

	for (std::map<int, Response *>::iterator it = clients.begin (); it != clients.end (); ++it)
	{
		/* is this client selected? */
		if (std::find (target.begin (), target.end (), it->second->GetIndex ()) == target.end ())
			continue;
		/* add epoll */
		event.events = EPOLLOUT;
		event.data.fd = it->first;
		if (epoll_ctl (epollFd, EPOLL_CTL_ADD, it->first, &event) < 0)
			throw std::runtime_error ("Server module: epoll_ctl: 326 line");
		requests.insert (std::pair<int, Request>(it->first, Request ()));
		requests[it->first].length = length;
		requests[it->first].offset = 0;
	}

	while (1)
	{
		ready = epoll_wait (epollFd, events, requests.size(), -1);
		if (ready < 0)
		{
			std::cout << number << " " << requests.size() << std::endl;
			std::cout << strerror (errno) << std::endl;
			throw std::runtime_error ("Server module: epoll_wait: 235 line");
		}

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
						throw std::runtime_error ("Server module: epoll_ctl: 230 line");
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

	void server_FL_start (int epoch, int * participants, int number)
	{
		server->FLStart (epoch, participants, number);
	}

	wchar_t ** server_FL_receive_weight_json ()
	{
		return server->FLReceiveWeight ();
	}

	void server_destroy ()
	{
		if (server)
			delete server;
	}
}
