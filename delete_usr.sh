#!/bin/bash

USR=$1

RET=`userdel -r $USR`
RET=$?

if [ "$RET" -eq 0 -o "$RET" -eq 6 ]; then
	exit 0
else
	exit $RET
fi
