#!/usr/bin/env bash
set -e

INET4PFXLEN="29"
INET6PFXLEN="64"

print_record()
{
	printf "route %s max %d as %u;\n" "$1" "$2" "$3"
}


# PROGRAM BEGIN

echo "# NeoNetwork ROA Tool"
(
for i in route*/* ; do
	source "$i"
	if [ "$TYPE" != PTP ]; then
		prefix="${i#route*/}"
		prefix="${prefix/,/\/}"
		pfxlen="${i#*,}"

		if [ "$TYPE" = "SUBNET" ]; then
			if [ "$pfxlen" -le "$INET4PFXLEN" ]||[ "$pfxlen" -ge 32 ]&&[ "$pfxlen" -le "$INET6PFXLEN" ]; then
				print_record "$prefix" "$INET4PFXLEN" "$ASN"
			fi
		elif [ "$TYPE" = "LO" ]; then
			print_record "$prefix" 32 "$ASN"
		fi
	fi
done
)
