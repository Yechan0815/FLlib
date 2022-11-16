#ifndef _F_PROTOCOL_H_
# define _F_PROTOCOL_H_

/* ######## ######## ######## */
/* # CODE # # BYTE # # BODY # */
/* ######## ######## ######## */

/* ######## ######## ######### ######### */
/* # CODE # # BYTE # # TOTAL # # INDEX # */
/* ######## ######## ######### ######### */

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
	Broadcast,
	/* end */
	Terminate
};

#endif
