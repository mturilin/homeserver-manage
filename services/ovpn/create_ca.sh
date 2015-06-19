#!/usr/bin/env bash

BASEDIR=$(dirname $0)
SERVICEDIR=$(dirname $BASEDIR)
OVPN_FOLDER=`$SERVICEDIR/homeserver get_var openvpn_folder`
echo Folder: $OVPN_FOLDER
OVPN_HOST=`$SERVICEDIR/homeserver get_var openvpn_host`
echo Host: $OVPN_HOST

sudo docker run -v $OVPN_FOLDER:/etc/openvpn/ --rm -it kylemanna/openvpn ovpn_genconfig -u udp://$OVPN_HOST
sudo docker run -v $OVPN_FOLDER:/etc/openvpn/ --rm -it kylemanna/openvpn ovpn_initpki

