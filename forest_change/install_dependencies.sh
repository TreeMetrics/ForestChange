#!/bin/sh

# --- Install Python and depencies--
python get-pip.py
pip install lxml shapely pyproj cached_property zipfile2


# --- Install SAGA and depencies--
apt-get update
apt-get install software-properties-common -y
add-apt-repository ppa:johanvdw/saga-gis -y
apt-get update
apt-get install saga=2.2.7+dfsg-0~ubuntugis~xenial -y
apt-get install python-saga


##################
# Compile/install GEOS. Taken from:
# http://grasswiki.osgeo.org/wiki/Compile_and_Install_Ubuntu#GEOS_2

cd /tmp
wget http://download.osgeo.org/geos/geos-3.6.2.tar.bz2
bunzip2 geos-3.6.2.tar.bz2
tar xvf  geos-3.6.2.tar

cd geos-3.6.2

./configure  &&  make  &&  make install
ldconfig

##########################################

# Compile & install proj.4. Taken from:
# http://grasswiki.osgeo.org/wiki/Compile_and_Install_Ubuntu#PROJ4

apt-get install subversion

cd /tmp
svn co http://svn.osgeo.org/metacrs/proj/branches/4.9/proj/

cd /tmp/proj/nad
wget http://download.osgeo.org/proj/proj-datumgrid-1.5.zip

unzip -o -q proj-datumgrid-1.5.zip

#make distclean

cd /tmp/proj/

./configure  &&  make  &&  make install && ldconfig

##########################################

# install gdal  - must happen after proj & geos
# taken from:
# http://grasswiki.osgeo.org/wiki/Compile_and_Install_Ubuntu#GDAL

# apt-get install libtiff4

cd /tmp
svn co https://svn.osgeo.org/gdal/branches/2.2/gdal gdal_stable

cd gdal_stable
#make distclean
CFLAGS="-g -Wall" LDFLAGS="-s" ./configure \
--with-png=internal \
--with-libtiff=internal \
--with-geotiff=internal \
--with-jpeg=internal \
--with-gif=internal \
--with-ecw=no \
--with-expat=yes \
--with-sqlite3=yes \
--with-geos=yes \
--with-python \
--with-libz=internal \
--with-netcdf \
--with-threads=yes \
--without-grass  \
--without-ogdi \
--with-xerces=yes

#with-pg=/usr/bin/pg_config \

make -j2  &&  make install  &&  ldconfig