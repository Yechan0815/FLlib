#include "Client.h"

static Client * client = nullptr;

/* coplien form */
Client::Client ()
{
}

Client::~Client ()
{	
	::close (socketFd);
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
		throw std::runtime_error ("client module: Signal: 44 line");
	signal = (int) buf[0];
	return signal;
}

int Client::Read (char ** out_buf)
{
	unsigned int length;
	unsigned int offset;
	unsigned int bytes;
	char buf[16];
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
		if ((bytes = ::read (socketFd, buffer + offset, length - offset)) < 0)
			throw std::runtime_error ("client module: Read: 66 line");
		offset += bytes;
	}
	buffer[length] = '\0';

	*out_buf = buffer;
	return offset;
}

void Client::Write (const char * buf, unsigned int length)
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

std::string ws_to_s (const std::wstring& wstr)
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

	void client_get_fl_data (int * selected, int * ignored, int * epoch)
	{
		char * buf;

		/* read epoch */
		client->Read (&buf);
		*selected = *((int *) buf);	
		*ignored = *((int *) (buf + 4));	
		if (epoch)
			*epoch = *((int *) (buf + 8));	

		delete[] buf;
	}

	void client_send_weight_json (wchar_t * weight)
	{
		std::string weight_s = ws_to_s (weight);
		char buf[6] = { (char) TCode::Unicast, 0 };

		*((unsigned int *) (buf + 1)) = weight_s.size ();
		/* send signal, bytes */
		client->Write(buf, 5);
		/* send weight */
		client->Write(weight_s.c_str (), weight_s.size ());
	}
	
	wchar_t * client_receive_weight_json ()
	{
		wchar_t * result;
		char * buf;

		if (client->Signal () != (int) TCode::Broadcast)
			throw std::runtime_error ("Server Module: server performed an undefined action during weight sharing");
		client->Read (&buf);
		result = new wchar_t[strlen (buf) + 2];
		mbstowcs (result, buf, strlen (buf) + 1);
		delete[] buf;

		return result;
	}

	void client_free_weight_json (wchar_t * arr)
	{
		delete[] arr;
	}

	void client_destroy ()
	{
		if (client)
			delete client;
	}
}
