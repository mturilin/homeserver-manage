#!/usr/bin/env python
from subprocess import CalledProcessError
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
    return 'true' in run_capture('sudo docker inspect --format="{{ .State.Running }}" %s  2> '
                                 '/dev/null' % name)


def container_exists(name):
    openvpn_containers = run_capture("sudo docker ps")
    return 'kylemanna/openvpn' in openvpn_containers and \
           'Dead:false' in run_capture('sudo docker inspect --format="{{ .State }}" %s  2> /dev/null' % name)

def run_capture(command):
    print "$", command
    try:
        return subprocess.check_output(command, shell=True)
    except CalledProcessError as err:
        print >> sys.stderr, err


def run(command):
    print "$", command
    try:
        return subprocess.call(command, shell=True)
    except CalledProcessError as err:
        print >> sys.stderr, err


def create_container(config):
    print "Creating config"
    if sudo_file_exists(config['openvpn_folder'] + '/openvpn.conf'):
        print "Path exists - skipping config creation"
    else:
        run(
            "sudo docker run -v %(openvpn_folder)s:/etc/openvpn/ --rm -it kylemanna/openvpn ovpn_genconfig -u "
            "udp://%(openvpn_host)s" % config)

    print "Creating CA"
    if sudo_file_exists(config['openvpn_folder'] + '/pki/ca.crt'):
        print "Path exists - skipping CA creation"
    else:
        run("sudo docker run -v %(openvpn_folder)s:/etc/openvpn/ --rm -it kylemanna/openvpn ovpn_initpki" % config)

    print "Checking Docker Container"
    if container_exists('openvpn'):
        print "Restarting Docker Container"
        run("sudo docker restart openvpn")
    else:
        print "Running Docker Container"
        run(
            "sudo docker run -v %(openvpn_folder)s:/etc/openvpn/ -d -p 1194:1194/udp --cap-add=NET_ADMIN"
            " -it --name=openvpn --restart=always kylemanna/openvpn" % config)


@click.group(invoke_without_command=True)
@click.option('--configfile', default='/etc/ansible/host_vars/localhost', help='path to the config file')
@click.pass_context
def cli(ctx, configfile):
    ctx.obj['configfile'] = configfile
    config = yaml.load(open(configfile))
    ctx.obj['config'] = config

    if ctx.invoked_subcommand is None:
        create_container(config)
        return


@click.command()
@click.argument('user_name')
@click.pass_context
def create_user(ctx, user_name):
    config = ctx.obj['config']

    print "Building user key for:", user_name
    run("sudo docker run -v %s:/etc/openvpn --rm -it kylemanna/openvpn easyrsa "
        "build-client-full %s "
        "nopass" % (config['openvpn_folder'], user_name))


@click.command()
@click.argument('user_name')
@click.argument('dest_dir', default=".")
@click.pass_context
def get_config(ctx, user_name, dest_dir):
    config = ctx.obj['config']
    openvpn_folder = config['openvpn_folder']

    print "Getting connection file for", user_name, "to", dest_dir + '/' + user_name + '.ovpn'
    run("sudo docker run -v %(openvpn_folder)s:/etc/openvpn --rm -it kylemanna/openvpn "
        "ovpn_getclient %(user_name)s > %(dest_dir)s/%(user_name)s.ovpn"
        % locals())


cli.add_command(create_user)
cli.add_command(get_config)

if __name__ == "__main__":
    cli(obj={})
