#ifndef _F_RESPONSE_H_
# define _F_RESPONSE_H_

class Response
{
public:
	Response ();
	~Response ();

	void SetSocket (int fd);

	void Init (unsigned int len = 16);
	void Buffering (char * buf, unsigned int bytes);

	void SetBHead (bool bhead);
	bool GetBHead ();

	void SetSize (unsigned int size);
	unsigned int GetSize ();

	void SetOffset (unsigned int offset);
	unsigned int GetOffset ();

	void SetIndex (int index);
	int GetIndex ();

	char * GetBuffer ();

private:
	void expand (unsigned int threshold);

private:
	bool head;

	int clientFd;
	int index;

	unsigned int size;
	unsigned int offset;

	char * buffer;
	unsigned int length;
};

#endif
