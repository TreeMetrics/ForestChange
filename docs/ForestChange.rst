.. _ForestChange_service:

^^^^^^^^^^^^^^^^^^^^^^
ForestChange
^^^^^^^^^^^^^^^^^^^^^^
The ForestChange_ service for eo4a Platform is a proof of concept to detect changes in areas with vegetation using  Sentinel-2 data.

The ForestChange_ service compare two Sentinel-2 datasets using NDVI and returns the changes above and below the change threshold defined by the user. This service uses the forest cover provided by the Irish Forestry Service as base layer for the analysis of the areas of forestry.

* *Input*:

  - ``s2_product_dir`` - Directory containing TWO L2A Sentinel-2 products for the same area and different dates. The Sentinel-2 products are typically an *output* from a previous service e.g. ``output_dir`` from the Copernicus_ service Sen2Three_ service.

  - ``threshold_change`` (*default is 20*) - Values 1 to 100. Threshold that will be used to set the change tolerance.  1 meaning no-changes and 100 everything changed.

  - ``additional_outputs`` (*optional*) - Values 1 or 0 (boolean). Additional output includes 10 m resolution TIF with the results of the change detection analysis. This output will be available for download, but not for display.

* *Output*:

  - ``output_dir`` - ForestChange_ output products directory including a TIF with the results of the change detection analysis with values 10 for reforested areas and 20 for deforested. This output is 60 m resolution. If ``additional_outputs`` is selected an additional output 10 m resolution will be generated. This output will be available for download, but not for display.

.. note::
    * Note that ONLY 2 datasets are allowed for each input. The datasets shall belong to the same area (same Sentinel-2 Tile Number).
    * Only Sentinel-2 data with a level of processing L2A is accepted.
    * Due to the large resource requirements of ForestChange_, 10 m resolution is not supported in the EO4Atlantic pathfinder, but this will be available as addtional output for download.
