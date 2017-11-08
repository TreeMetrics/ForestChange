#!/bin/sh

# --- Install SAGA and depencies--
echo ""
echo ""
echo "Installing SAGA!"
echo ""
echo ""
echo "sleep 10 s"
sleep 10s
echo "STEP ONE.........................................................................................................................apt-get update"
apt-get update
echo "STEP TWO.........................................................................................................................apt-get install software-properties-common -y"
apt-get install software-properties-common -y
echo "STEP THREE.........................................................................................................................add-apt-repository ppa:johanvdw/saga-gis -y"
add-apt-repository ppa:johanvdw/saga-gis -y
echo "STEP FOUR.........................................................................................................................apt-get update"
apt-get update
echo "STEP FIVE.........................................................................................................................apt-get install saga=2.2.7+dfsg-0~ubuntugis~xenial -y"
apt-get install saga=2.2.7+dfsg-0~ubuntugis~xenial -y
echo ""
echo ""
echo "Done!"
echo ""
echo ""