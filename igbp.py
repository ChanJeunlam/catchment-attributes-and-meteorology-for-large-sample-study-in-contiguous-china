import numpy as np
from tqdm import tqdm
import pandas as pd
from utils import *

'''
基于 MODIS MCD12Q1 产品 LC_Type1 计算流域每种土地覆盖类型所占比例
（Annual International Geosphere-Biosphere Programme (IGBP) classification）

Reference:
https://lpdaac.usgs.gov/products/mcd12q1v006/

Requirement:
(1) IGBP.tif: converted IGBP classification in raster form
(2) Catchment shapefiles
├── folder_shp
|   ├── outwtrshd_0000.shp
|   ├── outwtrshd_0000.dbf
|   ├── outwtrshd_0000.sbx
|   ├── outwtrshd_0000.cpg
|   ├── ...
'''


def modis_land_cover_igbp_number2name(index: int):
    names = ['Evergreen needleleaf tree',
             'Evergreen broadleaf tree',
             'Deciduous needleleaf tree',
             'Deciduous broadleaf tree',
             'Mixed forest',
             'Closed shrubland',
             'Open shrubland',
             'Woody savanna',
             'Savanna',
             'Grassland',
             'Permanent wetland',
             'Cropland',
             'Urban and built-up land',
             'Cropland/natural vegetaion',
             'Snow and ice',
             'Barren',
             'Water bodies']
    try:
        return names[index - 1]
    except IndexError:
        return 'nan'


def modis_land_cover_igbp_name2number(name: str):
    names = ['Evergreen needleleaf tree',
             'Evergreen broadleaf tree',
             'Deciduous needleleaf tree',
             'Deciduous broadleaf tree',
             'Mixed forest',
             'Closed shrubland',
             'Open shrubland',
             'Woody savanna',
             'Savanna',
             'Grassland',
             'Permanent wetland',
             'Cropland',
             'Urban and built-up land',
             'Cropland/natural vegetaion',
             'Snow and ice',
             'Barren',
             'Water bodies']
    return names.index(name)


def igbp_stats(shapefile: str, igbp_tif: str, nan_value=255):
    ''' 给定 shapefilem, 根据 Modis_IGBP 分类, 计算其 dom_land_cover, dom_land_cover_frac, forest_frac 三个参数

    Parameters
    ----------
    shapefile 要统计的 .shp 文件
    igbp_tif 已生成好的 igbp_yr.tif 文件, 生成方法见 Modis_v1.2.ipynb
    nan_value 默认 255

    Returns
    -------
    dict
    {'dom_land_cover': land_class_1st, 'dom_land_cover_frac': land_class_1st_frac, 'forest_frac': forest_frac}
    '''

    names = ['Evergreen needleleaf tree',
             'Evergreen broadleaf tree',
             'Deciduous needleleaf tree',
             'Deciduous broadleaf tree',
             'Mixed forest',
             'Closed shrubland',
             'Open shrubland',
             'Woody savanna',
             'Savanna',
             'Grassland',
             'Permanent wetland',
             'Cropland',
             'Urban and built-up land',
             'Cropland/natural vegetaion',
             'Snow and ice',
             'Barren',
             'Water bodies']

    res = extract_raster_by_shape_file(raster=igbp_tif, shape_file=shapefile, output_file=None)
    res = res[res != -9999].flatten()
    res_list = res[res != nan_value].flatten().tolist()
    res_str = [modis_land_cover_igbp_number2name(number) for number in res_list]
    land_class, count = np.unique(res_str, return_counts=True)
    land_class_rank = [x for _, x in sorted(zip(count, land_class), reverse=True) if x != 'nan']

    res = {}
    for name in names:
        res[name + '(fraction)'] = 0
    for num, name in zip(count, land_class):
        if name != 'nan':
            res[name + '(fraction)'] = num / np.sum(count)

    print('shapefile:', shapefile)
    print(res)
    return res


if __name__ == '__main__':
    igbp_tif = "./data/IGBP.tif"
    shp_dir = './shapefiles'
    out = './output/igbp.xlsx'

    res = {}
    for shape_file in tqdm(file for file in absolute_file_paths(shp_dir) if file.endswith('.shp')):
        res[shp_id(shape_file)] = igbp_stats(shapefile=shape_file, igbp_tif=igbp_tif)
    pd.DataFrame(res).T.to_excel(out)
