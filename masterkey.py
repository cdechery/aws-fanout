#!/usr/bin/python

import sys
import shlex
from threading import Timer
from subprocess import Popen
from subprocess import PIPE
from os.path import basename

SSH_TIMEOUT = 30 # in seconds

def run_shell(cmd):

    #print(cmd)
    #return (None, None, 0)

    global SSH_TIMEOUT

    proc = Popen(shlex.split(cmd), stdout=PIPE,\
        stderr=PIPE)

    kill_proc = lambda p: p.kill()
    timer = Timer(SSH_TIMEOUT, kill_proc, [proc])

    try:
        timer.start()
        stdout,stderr = proc.communicate()
        return (stdout,stderr,proc.returncode)
    finally:
        timer.cancel()


def add_key_to_server(privkey, pubkey, server):

    remote_pubkey = basename(pubkey)

    out,err,ret = run_shell('scp -i {} {} {}:~/{}'.format(privkey, pubkey, server, remote_pubkey))
    if ret != 0:
        return ('ERROR: cannot copy public key to remote server', err)

    out,err,ret = run_shell('ssh -i {} {} "grep -F -f {} .ssh/authorized_keys || cat {} >> .ssh/authorized_keys"'.format(privkey, server, remote_pubkey, remote_pubkey))
    if ret != 0:
        return ('ERROR: cannot add public key to authorized_keys', err)

    out,err,ret = run_shell('ssh -i {} {} "rm -rf {}"'.format(privkey, server, remote_pubkey))

    return (None, None)

def remove_key_from_server(privkey, pubkey, server):

    remote_pubkey = basename(pubkey)

    out,err,ret = run_shell('scp -i {} {} {}:~/{}'.format(privkey, pubkey, server, remote_pubkey))
    if ret != 0:
        return ('ERROR: cannot copy public key to remote server', err)

    out,err,ret = run_shell('ssh -i {} {} \'PUBKEY=`cat {}`; grep -v "$PUBKEY" .ssh/authorized_keys > tmpkeys; cat tmpkeys > .ssh/authorized_keys; rm -rf tmpkeys\''.format(privkey, server, remote_pubkey))
    if ret != 0:
        return ('ERROR: cannot remove public key from authorized_keys', err)

    out,err,ret = run_shell('ssh -i {} {} "rm -rf {}"'.format(privkey, server, remote_pubkey))

    return (None, None)


##################################
# Start of script main execution
##################################

def display_usage_and_quit():
    print(
        '## MasterKey Provision Tool ##' + \
        '\n\n' + \
        '  Usage: python masterkey.py <public_key>\n\n' +\
        '  The trustedservers.csv file must be correcly populated with the format below: \n'+\
        '  action,privatekeyA,server1,server2,server3\n'+\
        '  action,privatekeyB,server4,server5,server6\n'+\
        '  - action can be either A for add, D for delete\n'+\
        '  - you can use user@servername if needed\n\n'
        )
    exit(0)

params = sys.argv[1:]
public_key = None

if len(params) != 1:
    display_usage_and_quit()

try:
    public_key = params[0]
    with open(public_key, 'r') as myfile:
      data = myfile.read()
except:
    print('ERROR: cannot open pubkey file [{}]'.format(public_key))
    exit(1)

try:
    servers = open('trustedservers.csv', 'r')
except Exception as e:
    print('ERROR: cannot open trustedservers.csv file')
    exit(2)

line_num = 0

for line in servers.readlines():

    if line[0] == '#':
        continue

    line_num += 1

    line_parts = line.strip().split(',')
    action = line_parts[0]
    private_key = line_parts[1]
    servers = line_parts[2:]

    try:
        with open(private_key, 'r') as myfile:
          data = myfile.read()
    except:
        print('ERROR: cannot open privkey file [{}] for line #{}'.format(private_key, line_num))
        continue

    action = action.upper()
    if action not in ['A','D']:
        print('ERROR: Invalid action [{}], skipping line #{}'.format(action, line_num))
        continue

    if action == 'A':
        for server in servers:
            print('Adding {} to {} using {}'.format(public_key, server, private_key))
            (out,err) = add_key_to_server(private_key, public_key, server)
            if out:
                print('{} [server: {}, details: {}]'.format(out, server, err))
            else:
                print('Public key sucessfully added to {}'.format(server))
    else:
        for server in servers:
            print('Deleting {} from {} using {}'.format(public_key, server, private_key))
            (out,err) = remove_key_from_server(private_key, public_key, server)
            if out:
                print('{} [server: {}, details: {}]'.format(out, server, err))
            else:
                print('Public key sucessfully removed from {}'.format(server))

