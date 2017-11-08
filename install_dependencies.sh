#!/bin/sh

# --- Install SAGA and depencies--
apt-get update
apt-get install software-properties-common -y
add-apt-repository ppa:johanvdw/saga-gis -y
apt-get update
apt-get install saga=2.2.7+dfsg-0~ubuntugis~xenial -y
apt-get install python-saga
