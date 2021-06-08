# catchment-attributes-and-meteorology-for-large-sample-study-in-contiguous-china
This repository contains the complement code for paper: Zhen Hao, Jin Jin, Runliang Xia, Shimin Tian, &amp; Wushuang Yang. (2021). Catchment attributes and meteorology for large sample study in contiguous China (Version 1.5). http://doi.org/10.5281/zenodo.4704017

This repository is currently under development.

## Instruction:
### Forcing time series (within China)

1. Download the site observation data (access permission needed)


https://data.cma.cn/data/cdcdetail/dataCode/SURF_CLI_CHN_MUL_DAY_V3.0.html

The directory should be structured as follows:
```bash
├── Data  
|   ├── EVP  
|   |   ├── SURF_CLI_CHN_MUL_DAY-EVP-13240-195101.TXT  
|   ├── GST  
|   |   ├── ...  
|   ├── WIN  
|   |   ├── ...  
```

2. Interpolate site observation climate data to rasters (GeoTIFF)


In raster.py, change line 432-441, specify the output directory (will contain the interpolated rasters) and the root directory of the site observation data, and possibly other configurations. 
The default interpolation range covers the whole of China.
Interpolation can take hours to run. The resulting directory looks like this:

<img src=https://user-images.githubusercontent.com/46937286/121157146-e2690c80-c87b-11eb-800b-f734bc1d44d9.png alt="drawing" width="200"/>
<img src=https://user-images.githubusercontent.com/46937286/121157156-e432d000-c87b-11eb-96df-1a76a27f2ff6.png alt="drawing" width="800"/>

3. Calculate the catchment mean based on the interpolated rasters


In raster2catchment.py, change line 160-162, specify the path to the interpolated rasters, catchment shapefiles and the output directory.
The shapefile directory should look like this:

<img src=https://user-images.githubusercontent.com/46937286/121157208-ee54ce80-c87b-11eb-8ccb-0402a9eca27d.png alt="drawing" width="200"/>

in which a catchment identifier is separated by an underscore.
For each basin, a forcing.xlsx file is generated in the output directory.  e.g. "./forcing_time_series/basin_name/forcing.xlsx"

### Climate indicator
In climate.py, change line 110 and 111, specify the path to the forcing time series and the output dir. Run climate.py. 
Note that the program assumes the file path contains the  basin name (line 117: name = file.split('\\')[-2]).

### Lithology
1. Download the GLiM dataset: https://www.dropbox.com/s/9vuowtebp9f1iud/LiMW_GIS%202015.gdb.zip?dl=0
2. Import the dataset to ArcMap
3. Export GLiM to GeoTIFF format; we specify the cell size as 0.024424875
4. Reproject the exported GLiM to EPSG: 4326 using the following script:

> from utils import * <br>
> reproject_tif(path_glim_tif, path_output, out_crc='EPSG:4326') <br>

Run glim.py

The directory should be structured as follows:

```bash
├── glim.py
├── shapefiles
|   ├── 0000.shp
|   ├── 0001.shp
├── GlimRaster.tif
├── GLiMCateNumberMapping.csv
├── glim_short2longname.txt
```

Note: the program assumes the shapefile has a numeric identifier. e.g. ./shapefiles/0000.shp or ./shapefiles/basin_0000.shp
The resulting file will appear in the output dir.

### Land cover
Source data: https://lpdaac.usgs.gov/products/mcd12q1v006/
However, MODIS data is divided into different tiles, which is inconvenient for processing.
We have merged the MODIS product into a single tif which can be downloaded at:
[Zenodo]

Run igbp.py

Required forlder sturcture:
```bash
(1) IGBP.tif: converted IGBP classification in raster form
(2) 流域shapefile
├── folder_shp
|   ├── outwtrshd_0000.shp
|   ├── outwtrshd_0000.dbf
|   ├── outwtrshd_0000.sbx
|   ├── outwtrshd_0000.cpg
|   ├── ...
```

Note: the program assumes the shapefile has a numeric identifier. e.g. ./shapefiles/0000.shp or ./shapefiles/basin_0000.shp

The resulting file will appear in the output dir.

### Root depth
Run rooting_depth.py

Required folder structure:
```bash
(1) IGBP.tif: converted IGBP classification in raster form
(2) calculated_root_depth.txt: calculated root_depth 50/99 for each type of land cover based on Eq. (2) and Table 2 in (Zeng 2001)
(2) 流域shapefile
├── folder_shp
|   ├── outwtrshd_0000.shp
|   ├── outwtrshd_0000.dbf
|   ├── outwtrshd_0000.sbx
|   ├── outwtrshd_0000.cpg
|   ├── ...
```

### Topography
Download ASTER GDEM from https://asterweb.jpl.nasa.gov/gdem.asp; we recommend using NASA Earthdata.

Run topography.py

Required forlder sturcute:
```bash
(1) ASTER GDEM
├── folder_gdem
|   ├── ASTGTMV003_N34E111_dem.tif
|   ├── ASTGTMV003_N32E110_dem.tif
|   ├── ASTGTMV003_N33E109_dem.tif
|   ├── ASTGTMV003_N34E108_dem.tif
|   ├── ...

(2) 流域shapefile
├── folder_shp
|   ├── outwtrshd_0000.shp
|   ├── outwtrshd_0000.dbf
|   ├── outwtrshd_0000.sbx
|   ├── outwtrshd_0000.cpg
|   ├── ...
```

### LAI/NDVI
