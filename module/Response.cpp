#include "Response.h"

/* coplien form */
Response::Response () :
	size (-1),
	offset (0),
	buffer (nullptr),
	length (0)
{
}

Response::~Response ()
{
	if (buffer)
		delete[] buffer;
}

/* public */
void Response::SetSocket (int fd)
{
	clientFd = fd;
}

void Response::Init ()
{
	size = -1;
	offset = 0;

	length = 2;
	buffer = new char[length + 1];
}

void Response::Buffering (char * buf, unsigned int bytes)
{
	if (offset + bytes >= length)
		expand (offset + bytes);
	
	for (unsigned int i = 0; i < bytes; ++i)
		buffer[offset + i] = buf[i];
	offset += bytes;
}

void Response::SetSize (unsigned int size)
{
	this->size = size;
}

char * Response::GetBuffer ()
{
	buffer[offset] = 0;
	return buffer;
}

/* private */
void Response::expand (unsigned int threshold)
{
	char * newBuffer;
	unsigned int newLength;

	newLength = length;
	while (threshold >= newLength)
		newLength *= 2;

	newBuffer = new char[newLength + 1];
	for (unsigned int i = 0; i < offset; ++i)
		newBuffer[i] = buffer[i];

	delete[] buffer;

	buffer = newBuffer;
	length = newLength;
}
