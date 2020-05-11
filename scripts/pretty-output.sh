#!/usr/bin/env bash
set -e
	##########################################
	# =============== Colors =============== #
	##########################################

ESC='\033'
RESET="${ESC}[0m"	#Reset all attributes
BRIGHT="${ESC}[1m"	#Bright
DIM="${ESC}[2m"	#Dim
BLINK="${ESC}[5m"	#Blink
# Foreground Colours #
FBLACK="${ESC}[30m"	#Black
FRED="${ESC}[31m"	#Red
FGREEN="${ESC}[32m"	#Green
FYELLOW="${ESC}[33m"	#Yellow
FBLUE="${ESC}[34m"	#Blue
FMAGENTA="${ESC}[35m"	#Magenta
FCYAN="${ESC}[36m"	#Cyan
FWHITE="${ESC}[37m"	#White
# Background Colours #
BBLACK="${ESC}[40m"	#Black
BRED="${ESC}[41m"	#Red
BGREEN="${ESC}[42m"	#Green
BYELLOW="${ESC}[43m"	#Yellow
BBLUE="${ESC}[44m"	#Blue
BMAGENTA="${ESC}[45m"	#Magenta
BCYAN="${ESC}[46m"	#Cyan
BWHITE="${ESC}[47m"	#White

	#########################
	# Functions:		#
	# Make your life easier #
	#########################

# Error Message that stops the script
errmsg()
{
	echo -en "${BRED}>>${RESET} ${FMAGENTA}${*}${RESET}"
	return 1
}

# Normal Message
msg()
{
	echo -en "${BBLUE}>>${RESET} ${BRIGHT}${FGREEN}${*}${RESET}"
}

# Debug Level Verbose
dbgmsg()
{
	echo -en "${BRIGHT}${BBLUE}>>${RESET} ${BRIGHT}${FGREEN}${*}${RESET}"
}

# Verbose Message
vmsg()
{
	echo -en "${BRIGHT}${BBLUE}>>${RESET} ${BRIGHT}${FCYAN}${*}${RESET}"
}

# Formatted Output

# for TUN30
print_tun30()
{
	printf "${FGREEN}%-20s${RESET}|${FYELLOW}%10s${RESET}| ${FCYAN}%20s ${BRIGHT}${FBLUE}<--> ${FMAGENTA}%s${RESET}\n" \
		"$1" "$2" "$3" "$4"
}

print_subnet()
{
	printf "${FGREEN}%-20s${RESET}${BRIGHT}${FBLUE}|| ${FMAGENTA}%s${RESET}\n\t>> %s\n" \
		"$1" "$2" "$3"
}

print_ptp()
{
	upstream_ip="${1%~*}"
	downstream_ip="${1#$upstream_ip}"
	downstream_ip="${downstream_ip#*~}"
	upstream_ip="${upstream_ip#PTP/}"
	printf "${BRIGHT}${FGREEN}%-10s${RESET}| ${BRIGHT}${FYELLOW}%10s ${FBLUE}<<>> ${FYELLOW}%s${RESET}\n>>> ${FCYAN}%20s ${BRIGHT}${FBLUE}<--> ${FMAGENTA}%s${RESET}\n" \
		"$2" "$upstream_ip" "$downstream_ip" "$3" "$4"
}

print_lo()
{
	printf "${FGREEN}%-20s${RESET}${BRIGHT}${FBLUE}||${FMAGENTA}%24s${RESET} ${BRIGHT}${FBLUE}|| ${RESET}%s\n" \
		"$1" "$2" "$3"
}

#################
# PROGRAM BEGIN #
#################

if [ $# -lt 1 ]; then
	# Print usage
	errmsg \
		"Usage: table-output.sh <table type>\n" \
		"\n" \
		"	table types:\n" \
		"		asn, route, people, node\n"
fi

arg="$2"	# Optional argument

case "$1" in
asn)
	(
	cd asn
	for i in *; do
		msg "${i#asn/}\n"
		source "$i"

		printf "${BRIGHT}${FMAGENTA}%-16s${RESET}| ${BRIGHT}${FYELLOW}%s\n\t>> %s\n" \
			"$OWNER" "$NAME" "$DESC"
	done
	)
	;;
route)
	for i in route*/*; do
		subnet="${i#route*/}"
		subnet="${subnet/,/\/}"
		source "$i"
		case "$TYPE" in
			TUN30)	print_tun30	"$subnet" "$PROTO" "$UPSTREAM" "$DOWNSTREAM";;
			SUBNET)	print_subnet	"$subnet" "$NAME" "$DESC";;
			LO)	print_lo	"$subnet" "$NAME" "$DESC";;
			*)	errmsg "Invalid \$TYPE in $i\n";;
		esac
	done
	;;
people);;
node);;
*) errmsg "Invalid type\n";;
esac

# vim: set tabstop=8:softtabstop=8:shiftwidth=8
