#ifndef _F_PROTOCOL_H_
# define _F_PROTOCOL_H_

/* ######## ######## ######## */
/* # CODE # # BYTE # # BODY # */
/* ######## ######## ######## */

/* handshake */
/* ######## ######## ######### ######### */
/* # CODE # # BYTE # # TOTAL # # INDEX # */
/* ######## ######## ######### ######### */

/* select */
/* ######## ######## ######### */
/* # CODE # # BYTE # # EPOCH # */
/* ######## ######## ######### */

/* ignore */
/* ######## */
/* # CODE # */
/* ######## */

/* sned the weights of model (server <-> client) */
/* ######## ######## ########### ######## ########### ... */
/* # CODE # # BYTE # # WEIGHTS # # BYTE # # WEIGHTS # ... */
/* ######## ######## ########### ######## ########### ... */

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
