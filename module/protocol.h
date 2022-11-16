#ifndef _F_PROTOCOL_H_
# define _F_PROTOCOL_H_

/* ######## ######## ######## */
/* # CODE # # BYTE # # BODY # */
/* ######## ######## ######## */

/* transfer code */
enum class TCode
{
	/* handshake */
	SYN,
	ACK,
	/* round */
	Select,
	Ignore,
	/* model */
	Unicast,
	Broadcast
};

#endif
