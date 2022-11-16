#ifndef _F_REQUEST_H_
# define _F_REQUEST_H_

class Request
{
	friend class Server;
public:
	Request ();
	~Request ();

private:
	unsigned int length;
	unsigned int offset;
};

#endif
