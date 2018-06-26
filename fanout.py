#!/usr/bin/python

import sys
import shlex
from threading import Timer
from subprocess import Popen
from subprocess import PIPE

dl_create_s3 = 'aws s3 cp s3://oidigital/fanout/create_usr.sh .'
dl_delete_s3 = 'aws s3 cp s3://oidigital/fanout/delete_usr.sh .'

def run_shell(cmd, timeout_sec=60):

    proc = Popen(shlex.split(cmd), stdout=PIPE,\
        stderr=PIPE)

    kill_proc = lambda p: p.kill()
    timer = Timer(timeout_sec, kill_proc, [proc])

    try:
        timer.start()
        stdout,stderr = proc.communicate()
        return (stdout,stderr,proc.returncode)
    finally:
        timer.cancel()

def create_local_user(user, comment, updatekey=False):

    out,err,ret = run_shell(dl_create_s3)
    if ret != 0:
        print('Error copying the create_usr.sh script from S3')
        sys.exit(1)

    out,err,ret = run_shell('chmod 750 ./create_usr.sh')
    if ret != 0:
        print('Error setting permissions for create_usr.sh on {}'.format(server))
        sys.exit(1)

    if updatekey:
        updatekey = " --updatekey"
    else:
        updatekey = ""

    out,err,ret = run_shell('sudo ./create_usr.sh {} "{}"{}'.format(user, comment, updatekey))

    return ret==0

def delete_local_user(user):

    out,err,ret = run_shell(dl_delete_s3)
    if ret != 0:
        print('Error copying the delete_usr.sh script from S3')
        sys.exit(1)

    out,err,ret = run_shell('chmod 750 ./delete_usr.sh')
    if ret != 0:
        print('Error setting permissions for delete_usr.sh')
        sys.exit(1)

    out,err,ret = run_shell('sudo ./delete_usr.sh {}'.format(user))

    return ret==0

def create_remote_user(user, comment, server, updatekey=False):

    out,err,ret = run_shell('ssh {} \'{}\''.format(server, dl_create_s3))
    if ret != 0:
        print('Error copying the create_usr.sh script from S3 on {}'.format(server))
        sys.exit(1)

    out,err,ret = run_shell('ssh {} "chmod 750 ~/create_usr.sh"'.format(server))
    if ret != 0:
        print('Error setting permissions for create_usr.sh on {}'.format(server))
        sys.exit(1)

    if updatekey:
        updatekey = " --updatekey"
    else:
        updatekey = ""

    out,err,ret = run_shell('ssh {} "sudo ~/create_usr.sh {} \'{}\'{}"'.format(server, user, comment, updatekey))

    return ret==0

def delete_remote_user(server, user):

    out,err,ret = run_shell('ssh {} \'{}\''.format(server, dl_delete_s3))
    if ret != 0:
        print('Error copying the delete_usr.sh script from S3 on {}'.format(server))
        sys.exit(1)

    out,err,ret = run_shell('ssh {} "chmod 750 ~/delete_usr.sh"'.format(server))
    if ret != 0:
        print('Error setting permissions for delete_usr.sh on {}'.format(server))
        sys.exit(1)

    out,err,ret = run_shell('ssh {} "sudo ~/delete_usr.sh {}"'.format(server, user))

    return ret==0


def add_user_to_group(server, user, group):

    out,err,ret = run_shell('ssh {} \'sudo su - \
        -c "usermod -G {} {}"\''.format(server, group, user))

    return ret==0


##################################
# Start of script main execution
##################################

permissions = open('permissions.csv','r')

for perm in permissions.readlines():
    if perm[0] == '#':
        continue

    perm_parts = perm.split(',')
    user = perm_parts[0]
    comment = perm_parts[1]
    servers = perm_parts[2:]

    updatekey = False
    if perm[0] == '!':
        updatekey = True
        user = user[1:]

    delete = False
    if perm[0] == '-':
        delete = True
        user = user[1:]

    print('Processing user: '+user)
    if delete:
        if delete_local_user(user):
            print(' - deleted (or non existent) local user')
        else:
            print(' - error deleting local user')
            continue
    else:
        if create_local_user(user, comment, updatekey):
            print(' - local user created')
        else:
            print(' - error creating local user')
            continue

    for server in servers:

        server = server.strip()
        server_groups = server.split(':')
        server_has_groups = False

        if len(server_groups) > 1:
            server_has_groups = True
            server = server_groups[0]
            server_groups = server_groups[1:]

        if delete:
            if delete_remote_user(server, user):
                print(' - deleted (or non existent) from server '+server)
            else:
                print(' - error deleting remote user on '+server)
            continue

        if create_remote_user(user, comment, server, updatekey):
            print(' - granted access to server '+server)
        else:
            print(' - error granting access to server '+server)

        if server_has_groups:
            for group in server_groups:
                if add_user_to_group(server,user,group):
                    print('   + group: '+group)
                else:
                    print('   - could not add user to group '+group)
        else:
            print('   (no groups)')
