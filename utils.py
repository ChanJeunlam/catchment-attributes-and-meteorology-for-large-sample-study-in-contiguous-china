import os
import re
import datetime
import numpy as np
import pandas as pd
import pickle
import gdal, osr

from tqdm import tqdm
import time
import fiona
import netCDF4
from netCDF4 import Dataset
import geopandas as gpd
import rasterio
import rasterio.mask
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling


def geotif_from_array(array: np.array, lat_start: float, lat_end: float, lon_start: float, lon_end: float,
                      degree: float, output_file: str):
    """ 将一个 numpy array 写入一个带有位置信息的 tif 文件，默认使用 wgs84 坐标系
    array: 要写入 tif 的变量，其 shape 应该和 lats 和 lons 对应
    lat_start: 起始维度，可参考 arcmap 生成的栅格文件 source 属性
    lat_end: 起始经度，可参考 arcmap 生成的栅格文件 source 属性
    lon_start, lon_end: 纬度同上
    degree: 输出栅格的一个网格的度数
    output_file: 输出 .tif 文件的路径
    # >>> geotif_from_array(array=res, lat_start=19.94174, lat_end=49.18826, lon_start=75.46174, lon_end=130.5756, degree=0.11652\
    # , output_file='results/tmp.tif')
    """
    nx, ny = array.shape
    mag_grid = np.reshape(array, (nx, ny), order='F')  # !!!
    mag_grid = np.float64(mag_grid)
    lats = np.linspace(start=lat_start, stop=lat_end, num=mag_grid.shape[0])
    lons = np.linspace(start=lon_start, stop=lon_end, num=mag_grid.shape[1])
    assert len(lats) == mag_grid.shape[0]
    assert len(lons) == mag_grid.shape[1]
    xres = lons[1] - lons[0]
    yres = lats[1] - lats[0]
    ysize = len(lats)
    xsize = len(lons)
    driver = gdal.GetDriverByName('GTiff')
    ds = driver.Create(output_file, xsize, ysize, 1, gdal.GDT_Float32)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    ds.SetProjection(srs.ExportToWkt())
    gt = [lon_start, xres, 0, lat_start, 0, yres]
    ds.SetGeoTransform(gt)
    outband = ds.GetRasterBand(1)
    outband.SetStatistics(np.min(mag_grid), np.max(mag_grid), np.average(mag_grid), np.std(mag_grid))
    outband.WriteArray(mag_grid)
    ds = None


def shp_id(shpfile: str):
    return re.findall(r'[\d]+', shpfile)[-1]


def absolute_file_paths(directory):
    """

    Parameters
    ----------
    directory: 文件夹路径

    Returns
    -------
    list:
        文件夹及其子文件夹内的所有文件的路径
    """

    def nest(nest_directory):
        for path, _, filenames in os.walk(nest_directory):
            for f in filenames:
                yield os.path.abspath(os.path.join(path, f))

    return list(nest(directory))


def reproject_tif(src_tif: str, out_tif: str, out_crc='EPSG:4326'):
    """

    Parameters
    ----------
    src_tif: 源坐标系 .tif 文件路径
    out_tif: 输出坐标系 .tif 文件路径
    out_crc: 输出坐标系, 默认 EPSG:4326
    """
    with rasterio.open(src_tif) as src:
        transform, width, height = calculate_default_transform(
            src.crs, out_crc, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': out_crc,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.open(out_tif, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=out_crc,
                    resampling=Resampling.nearest)


def merge_tifs(tif_files: list, outfile: str):
    """
    Parameters
    ----------
    tif_files: .tif 文件路径列表
    outfile: 输出 .tif 文件路径
    """
    src_files_to_mosaic = []
    for fp in tif_files:
        src = rasterio.open(fp)
        src_files_to_mosaic.append(src)
    mosaic, out_trans = merge(src_files_to_mosaic)
    out_meta = src.meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": mosaic.shape[1],
                     "width": mosaic.shape[2],
                     "transform": out_trans,
                     "crs": "EPSG:4326"})
    with rasterio.open(outfile, "w", **out_meta) as dest:
        dest.write(mosaic)


def extract_raster_by_shape_file(raster: str, shape_file: str, output_file=None):
    """ 抽取 GeoTIFF 文件中的给定区域数据，返回数组
    Parameters
    ----------
    nodata: 指定 nodata 的值, 不在抽取范围内的值被标记为 nodata
    output_file: 输出 .tif 文件路径, None 不输出
    raster: .tif 文件的路径，要求坐标系为 WGS84 （EPSG:4326）
    shape_file: .shp 文件的路径，要求坐标系为 WGS84 （EPSG:4326）
    """
    with fiona.open(shape_file, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
    with rasterio.open(raster) as src:
        out_image, out_transform = rasterio.mask.mask(src, shapes, nodata=-9999, crop=True)
        out_meta = src.meta
    if output_file is None:
        return out_image
    else:
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})
        with rasterio.open(output_file, "w", **out_meta) as dest:
            dest.write(out_image)
        return out_image


def zonal_stats_singletif(tif_file: str, shape_file: str):
    """ 输入一个 .shp 文件和一个 .tif 文件, 根据 .shp 文件对 .tif 文件抽取栅格并区域统计
    """
    res = extract_raster_by_shape_file(tif_file, shape_file).flatten()
    res = res[res != -9999]
    res = res[~np.isnan(res)]
    if len(res) > 0:
        return np.mean(res)
    else:
        return np.nan
