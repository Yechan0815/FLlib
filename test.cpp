#define EXPORT

#include <iostream>
#include <unistd.h>

class testclass
{
public:
	int a;
	int b;
	int c;

	testclass()
	{
		std::cout << ";constructor" << std::endl;
	}

	~testclass()
	{
		std::cout << ";destructor" << std::endl;
	}

	void calc()
	{
		c = a + b;
	}
};

static testclass * stest;

extern "C"
{
	void alloc_t()
    {
		stest = new testclass;
    }

	void set(int a, int b)
	{
		stest->a = a;
		stest->b = b;
	}

	void de_t()
    {
		delete stest;
    }

	int calc()
	{
		stest->calc();
		sleep(3);
		return stest->c;
	}
}
