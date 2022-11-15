#ifndef _F_RESPONSE_H_
# define _F_RESPONSE_H_

class Response
{
public:
	Response ();
	~Response ();

	void SetSocket (int fd);

	void Init ();
	void Buffering (char * buf, unsigned int bytes);

	void SetSize (unsigned int size);

	char * GetBuffer ();

private:
	void expand (unsigned int threshold);

private:
	int clientFd;

	unsigned int size;
	unsigned int offset;

	char * buffer;
	unsigned int length;
};

#endif
