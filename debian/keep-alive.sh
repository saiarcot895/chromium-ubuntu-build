#!/bin/sh

# Simple keep-alive script echoing the date on stdout
# This is needed to prevent the builders from killing a build
# staying too long without producing outputs, like while
# linking chromium with ld-bfd.
#
# Usage:
#    keep-alive.sh start &
#    some actions...
#    keep-alive.sh stop
#
# Authors:
#  Fabien Tassin <fta@sofaraway.org>
# License: GPLv2 or later

ACTION=$1
LOCK=/var/tmp/k-a.lock
INTERVAL=5
LINTERVAL=300

case $ACTION in
 start)
   echo $$ > $LOCK
   T0=$(date +%s)
   T1=0
   while [ 1 ] ; do
     if [ ! -f $LOCK ] ; then
       break
     fi
     T2=$(date +%s)
     if [ $((T2-T1)) -ge $LINTERVAL ] ; then
       DELTA=$((T2-T0))
       FREE=$(free -mo | cut -c1-6,30-40 | tail -2 | awk '{ print "Free " $1 " " $2 "M" } ' | tr '\n' ' ')
       echo "[keep-alive] $(date) ($((DELTA/60)) min) [ $FREE]"
       T1=$T2
     fi
     sleep $INTERVAL
   done
   exit 0
   ;;
 stop)
   PID=$(cat $LOCK)
   rm -f $LOCK
   exit 0
   ;;
 *)
   echo "Usage: $(basename $0) [start|stop]"
   exit 1
esac
