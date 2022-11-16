#include "Client.h"

static Client * client = nullptr;

/* coplien form */
Client::Client ()
{
}

Client::~Client ()
{	
}

/* public */
bool Client::Init ()
{
	if ((socketFd = socket (AF_INET, SOCK_STREAM, 0)) == -1)
		return false;
	return true;
}

bool Client::Connect (const char * host, int port)
{
	address.sin_family = AF_INET;
	address.sin_addr.s_addr = inet_addr (host);
	address.sin_port = htons (port);

	if (::connect (socketFd, (struct sockaddr *) &address, sizeof (address)) == -1)
	{
		std::cout << strerror(errno) << std::endl;
		return false;
	}
	
	return true;
}

int Client::Signal ()
{
	char buf[2];
	int bytes;
	int signal;

	if ((bytes = ::read (socketFd, buf, 1)) < 0)
		throw std::runtime_error ("client module: Signal: 49 line");
	signal = (int) buf[0];
	return signal;
}

int Client::Read (char ** out_buf)
{
	char buf[2049];	
	unsigned int length;
	unsigned int offset;
	unsigned int bytes;
	char *buffer;

	/* get length */
	if ((bytes = ::read (socketFd, buf, 4)) < 0)
		throw std::runtime_error ("client module: Read: 58 line");
	length = *((unsigned int *) buf);
	/* read body */
	offset = 0;
	buffer = new char[length + 1];
	while (offset != length)
	{
		if ((bytes = ::read (socketFd, buf, length - offset)) < 0)
			throw std::runtime_error ("client module: Read: 67 line");
		for (unsigned int i = 0; i < bytes; ++i)
			buffer[offset + i] = buf[i];
		offset += bytes;
	}

	*out_buf = buffer;
	return offset;
}

void Client::Write (char * buf, unsigned int length)
{
	unsigned int offset;
	unsigned int bytes;
	
	offset = 0;
	while (offset != length)
	{
		if ((bytes = ::write (socketFd, buf + offset, length - offset)) < 0)
			throw std::runtime_error ("client module: Write: 91 line");
		offset += bytes;
	}
}

std::string ws_to_s(const std::wstring& wstr)
{
    std::wstring_convert<std::codecvt_utf8<wchar_t>, wchar_t> converter;

    return converter.to_bytes(wstr);
}

extern "C"
{
	bool client_init ()
	{
		if (client)
			return false;

		client = new Client;
		return client->Init ();
	}

	bool client_connect (wchar_t * host, int port)
	{
		return client->Connect (ws_to_s (host).c_str(), port);
	}

	void client_handshake (int * total, int * index)
	{
		char ack_buf[2] = { (char) TCode::ACK, 0 };
		char * buf;

		/* SYN from server */
		if (client->Signal () != (int) TCode::SYN)
		{
			*total = -1;
			*index = -1;
			return;
		}
		/* read index */
		client->Read (&buf);
		*total = *((int *) buf);
		*index = *((int *) (buf + 4));
		/* destroy */
		delete[] buf;
		/* send ACK */
		client->Write(ack_buf, 1);
	}

	int client_signal ()
	{
		return client->Signal ();
	}

	void client_destroy ()
	{
		if (client)
			delete client;
	}
}
