#!/bin/bash

USR2AUTH=$1
USRCOMM=$2
ACTION=$3

# Create user if one does not exist
grep ${USR2AUTH} /etc/passwd > /dev/null
if [ ! $? == 0 ]; then
    useradd -d /home/$USR2AUTH -m -s /bin/bash -c "$USRCOMM" $USR2AUTH
else
    if [ "$ACTION" != "--updatekey" ]; then
        echo "User already exists"
        exit 0
    fi
fi

USRHOME=/home/$USR2AUTH

if [ ! -d /home/$USR2AUTH/.ssh ]; then
  mkdir $USRHOME/.ssh
  chown $USR2AUTH:users $USRHOME/.ssh
  chmod 700 $USRHOME/.ssh
fi

# Copy key to authorized_keys
aws s3 cp s3://oidigital/fanout/public_keys/authorized_keys.$USR2AUTH . > /dev/null
if [ "$?" -ne 0 ]; then
	exit 1
else
	chmod 600 authorized_keys.$USR2AUTH
	sudo chown $USR2AUTH:$USR2AUTH authorized_keys.$USR2AUTH
	sudo mv authorized_keys.$USR2AUTH $USRHOME/.ssh/authorized_keys
fi

