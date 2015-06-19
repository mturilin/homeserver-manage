#!/usr/bin/env python
import sys

try:
    import click
except ImportError:
    print >> sys.stderr, "Homeserver: Error, can't find command line libraries. Please activate virtualenv!"

import os
import yaml
import click
import subprocess


def sudo_file_exists(filename):
    res = subprocess.check_output("sudo ls %s" % filename, shell=True)
    return filename in res



def container_is_running(name):
    return 'true' in subprocess.check_output('sudo docker inspect --format="{{ .State.Running }}" %s  2> '
                                             '/dev/null' % name, shell=True)

def container_exists(name):
    return 'Dead:false' in subprocess.check_output('sudo docker inspect --format="{{ .State }}" %s  2> '
                                             '/dev/null' % name, shell=True)

@click.command()
@click.option('--configfile', default='/etc/ansible/host_vars/localhost', help='path to the config file')
def cli(configfile):
    # if os.getuid() != 0:
    #     print >> sys.stderr, "This script should be run only as sudo"
    #     sys.exit(1)
    #
    config = yaml.load(open(configfile))

    print "Creating config"
    if sudo_file_exists(config['openvpn_folder'] + '/openvpn.conf'):
        print "Path exists - skipping config creation"
    else:
        subprocess.call(
            "sudo docker run -v %(openvpn_folder)s:/etc/openvpn/ --rm -it kylemanna/openvpn ovpn_genconfig -u "
            "udp://%(openvpn_host)s" % config, shell=True)

    print "Creating CA"
    if sudo_file_exists(config['openvpn_folder'] + '/pki/ca.crt'):
        print "Path exists - skipping CA creation"
    else:
        subprocess.call(
            "sudo docker run -v %(openvpn_folder)s:/etc/openvpn/ --rm -it kylemanna/openvpn ovpn_initpki" % config,
            shell=True)

    print "Checking Docker Container"
    if container_exists('openvpn'):
        print "Restarting Docker Container"
        subprocess.call("sudo docker restart openvpn", shell=True)
    else:
        print "Running Docker Container"
        subprocess.call(
            "sudo docker run -v %(openvpn_folder)s:/etc/openvpn/ -d -p 1194:1194/udp --cap-add=NET_ADMIN"
            " -it --name=openvpn --restart=always kylemanna/openvpn" % config, shell=True)


if __name__ == "__main__":
    cli()
