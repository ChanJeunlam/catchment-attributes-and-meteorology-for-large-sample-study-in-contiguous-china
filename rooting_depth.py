import os, datetime, subprocess, shutil, sys
import numpy as np
import pandas as pd
from tqdm import tqdm
from utils import *

'''
基于 MODIS IGBP 分类计算流域有效根深分布 (Zeng 2001)

Reference:
Zeng, X. (2001). "Global vegetation root distribution for land modeling." Journal of Hydrometeorology 2(5): 525-530.
https://lpdaac.usgs.gov/products/mcd12q1v006/

Requirement:
(1) IGBP.tif: converted IGBP classification in raster form
(2) calculated_root_depth.txt: calculated root_depth 50/99 for each type of land cover based on Eq. (2) and Table 2 in (Zeng 2001)
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
    return names[index - 1]


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


class DepthMapper():
    def __init__(self, root_depth_file: str):
        self.land_root_depth = pd.read_table(root_depth_file, sep=',')

    def igbp2depth50(self, igbp_index: int):
        name = modis_land_cover_igbp_number2name(igbp_index)
        return self.land_root_depth[self.land_root_depth['land'] == name]['50'].values[0]

    def igbp2depth99(self, igbp_index: int):
        name = modis_land_cover_igbp_number2name(igbp_index)
        return self.land_root_depth[self.land_root_depth['land'] == name]['99'].values[0]


def root_depth_50_99_stats(shape_file: str, igbp_tif: str, depth_mapper: DepthMapper):
    ''' the arithmetic mean of catchment effective rooting depth for root_fraction_percentiles=50/99
        对给定的 shapefile, 根据 IGBP 分类, 计算每一个 grid 的有效根深 (root_fraction_percentiles=50/99), 统计算数均值

    Parameters
    ----------
    shape_file 要统计的 shapefile
    igbp_tif converted IGBP classification in raster form
    depth_mapper DepthMapper 对象, 存储了 IGBP 到 effective depth 的映射

    Returns
    -------
    dict
    {'root_depth_50': np.mean(depth50), 'root_depth_99': np.mean(depth99)}
    '''
    res = extract_raster_by_shape_file(raster=igbp_tif, shape_file=shape_file, output_file=None)
    res = res[res != -9999]
    res_list = res[res != 255].flatten().tolist()
    print('mapping igbp classification to effective rooting depth for each pixel')
    depth50 = [depth_mapper.igbp2depth50(index) for index in tqdm(res_list, position=0, leave=True, file=sys.stdout)]
    depth99 = [depth_mapper.igbp2depth99(index) for index in tqdm(res_list, position=0, leave=True, file=sys.stdout)]
    return {'root_depth_50': np.mean(depth50), 'root_depth_99': np.mean(depth99)}


if __name__ == '__main__':
    igbp_tif = './data/igbp.tif'
    root_depth = "./calculated_root_depth.txt"
    shp_dir = './shapefiles'
    out = './output/root_depth.xlsx'
    depth_mapper = DepthMapper(root_depth)

    res = {}
    for shape_file in [file for file in absolute_file_paths(shp_dir) if file.endswith('.shp')]:
        res[shp_id(shape_file)] = root_depth_50_99_stats(shape_file, igbp_tif, depth_mapper)
    pd.DataFrame(res).T.to_excel(out, header=False, index=False)
