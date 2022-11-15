#ifndef _F_PROTOCOL_H_
# define _F_PROTOCOL_H_

/* transfer code */
enum class TCode
{
	/* Round */
	Select,
	Ignore,
	/* Model */
	Unicast,
	Broadcast
};

#endif
