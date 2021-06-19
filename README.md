# catchment-attributes-and-meteorology-for-large-sample-study-in-contiguous-china
This repository contains the complement code for paper: Zhen Hao, Jin Jin, Runliang Xia, Shimin Tian, &amp; Wushuang Yang. (2021). Catchment attributes and meteorology for large sample study in contiguous China (Version 1.5). http://doi.org/10.5281/zenodo.4704017

## Instruction:
### Meteorological time series:

1. Download the situ observations meteorological data (access permission needed): https://data.cma.cn/data/cdcdetail/dataCode/SURF_CLI_CHN_MUL_DAY_V3.0.html. The data directory should be structured as follows:
```bash
├── Data  
|   ├── EVP  
|   |   ├── SURF_CLI_CHN_MUL_DAY-EVP-13240-195101.TXT  
|   ├── GST  
|   |   ├── ...  
|   ├── WIN  
|   |   ├── ...  
```
2. Interpolate site observation climate data to rasters (GeoTIFF). In raster.py, change line 432-441, specify the output directory (will contain the interpolated rasters) and the root directory of the situ observation meteorological data, and possibly other configurations (e.g. resolution and spatial range of interpolation). The default interpolation range covers the whole of China. Note: interpolation can take hours to run.
3. Calculate the catchment means based on the interpolated rasters. In raster2catchment.py, change line 160-162, specify the path to the interpolated rasters (step 2), catchment shapefiles and the output directory. For the name of the catchment shapefiles, the catchment identifier should be separated by an underscore. And note that the shapefile should have a numeric identifier, e.g. "./shapefiles/0000.shp" or "./shapefiles/basin_0000.shp". For each basin, a "forcing.xlsx" file will be generated in the output directory.  e.g. "./forcing_time_series/basin_name/forcing.xlsx"

### Climate indicator:
In climate.py, change line 110 and 111, specify the path to the forcing time series (last step) and the output dir (will contain the climate statistic file). Run climate.py. 
Note that the script assumes the file path contains the basin name (line 117: name = file.split('\\')[-2]).

### Lithology:
1. Download the GLiM dataset: https://www.dropbox.com/s/9vuowtebp9f1iud/LiMW_GIS%202015.gdb.zip?dl=0
2. Import the dataset to ArcMap/QGis
3. Export GLiM to GeoTIFF format; we specify the cell size as 0.024424875. Using ArcMap/QGis is not necessary; the aim is to convert GliM to a raster form for processing.
4. Reproject the exported GLiM to EPSG: 4326 using the following script:

> from utils import * <br>
> reproject_tif(path_glim_tif, path_output, out_crc='EPSG:4326') <br>

5. Run glim.py. The resulting file will appear in the specified output directory. The data directory should be structured as follows:

```bash
├── glim.py
├── shapefiles
|   ├── 0000.shp
|   ├── 0001.shp
├── GlimRaster.tif
├── GLiMCateNumberMapping.csv
├── glim_short2longname.txt
```

### Land cover:
1. Source data: https://lpdaac.usgs.gov/products/mcd12q1v006/. However, MODIS data is divided into different tiles, which is inconvenient for processing. We have merged the MODIS product into a single tif which can be downloaded here: [Zenodo, tbd]. Download the processed MODIS data (IGBP.tif).
2. Run igbp.py. The resulting file will appear in the output-dir. Required data folder structure:
```bash
(1) IGBP.tif: converted IGBP classification in raster form
(2) catchment shapefiles
├── folder_shp
|   ├── outwtrshd_0000.shp
|   ├── outwtrshd_0000.dbf
|   ├── outwtrshd_0000.sbx
|   ├── outwtrshd_0000.cpg
|   ├── ...
```

### Root depth:
Run rooting_depth.py. Required folder structure:
```bash
(1) IGBP.tif: converted IGBP classification in raster form
(2) calculated_root_depth.txt: calculated root_depth 50/99 for each type of land cover based on Eq. (2) and Table 2 in (Zeng 2001)
(2) catchement shapefiles
├── folder_shp
|   ├── outwtrshd_0000.shp
|   ├── outwtrshd_0000.dbf
|   ├── outwtrshd_0000.sbx
|   ├── outwtrshd_0000.cpg
|   ├── ...
```

### Topography:
1. Download ASTER GDEM from https://asterweb.jpl.nasa.gov/gdem.asp; we recommend using NASA Earthdata. 
2. Run topography.py. Required folder structure:
```bash
(1) ASTER GDEM
├── folder_gdem
|   ├── ASTGTMV003_N34E111_dem.tif
|   ├── ASTGTMV003_N32E110_dem.tif
|   ├── ASTGTMV003_N33E109_dem.tif
|   ├── ASTGTMV003_N34E108_dem.tif
|   ├── ...

(2) catchment shapefiles
├── folder_shp
|   ├── outwtrshd_0000.shp
|   ├── outwtrshd_0000.dbf
|   ├── outwtrshd_0000.sbx
|   ├── outwtrshd_0000.cpg
|   ├── ...
```

### LAI/NDVI:

1. Download modis product: https://lpdaac.usgs.gov/products/mcd15a3hv006/ (for LAI) and https://lpdaac.usgs.gov/products/mod13q1v006/ (for NDVI). 
2. The source data are in hdfs format. The provided script first find needed hdfs tiles for the given catchment and merge them. Then perform zonal statistics to get catchment-averaged values. Put the downloaded hdfs files into the folder ./MODIS/MOD13Q1[MCD15A3] and created an output folder e.g. ./output/ndvi, and run the code lai.py [ndvi.py].


