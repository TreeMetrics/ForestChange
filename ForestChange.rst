.. slug: index
.. date: 2018-01-30
.. tags: forest change

#################################
EO4Atlantic Forest Change Service
#################################

*************
forest_change
*************

========
SYNOPSIS
========
Forest change detection service for eo4a Platform.
This services perform change detection between two Sentinel-2 datasets in forest areas.
The service use the forest cover provided by the Irish Forestry Service to restrict the analysis to areas of forestry.

===========
DESCRIPTION
===========

General options
***************

s2_product_zip_newer
--------------------
Full path to newer dataset of Sentinel-2 product file (ZIP format). Data type: string.
Data format for SENTINEL-2 products shall be made available in SENTINEL-SAFE format.
It is recommended to use Sen2Three before run forest_change in order to have a cloud-free area.

s2_product_zip_older
--------------------
Full path to older dataset of Sentinel-2 product file (ZIP format). Data type: string.
Data format for SENTINEL-2 products shall be made available in SENTINEL-SAFE format.
It is recommended to use Sen2Three before run forest_change in order to have a cloud-free area.

destfile
--------
Full path to destination file name in ".tif" format. Data type: string.


Advanced options
****************

change_threshold
----------------
Change threshold 0-100. Default is 20. Data type: integer.
This threshold specifies the sensitivity to change as percentage of the change index calculated by the system.

tile_size
---------
Tile size. Default is 1000. Data type: integer.
Splits the dataset into tiles with side of this length (pixels) during the analysis in order to improve the performance.
This can be adjusted for higher resolution datasets.


Outputs
*******
destfile
--------
ForestChange output is a .tif  with 1 and 0 values, indicating the areas that have change (value 1) and the areas
that have not been changed (value 2). What is considered change can be configured using the "change_threshold" parameter.

