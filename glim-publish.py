import numpy as np
import pandas as pd
from tqdm import tqdm
import re
import os
import fiona
import rasterio

'''

基于 GliM 数据集进行区域岩性比例统计。
Reference: Hartmann, J., Moosdorf, N., 2012. The new global lithological map database GLiM: A representation of rock 
properties at the Earth surface. Geochemistry, Geophysics, Geosystems, 13. DOI: 10.1029/2012GC004370

Requirement: 
GlimRaster.tif: converted GliM in raster form (you can use ArcMap/QGis to complete this operation, we cannot directly share the converted data due to copyright issues)
GLiMCateNumberMapping.csv: mapping number to lithology category
glim_short2longname.txt: mapping short name to long name of lithology categories

The directory should be structured as follows:

├── glim.py
├── shapefiles
|   ├── 0000.shp
|   ├── 0001.shp
├── GlimRaster.tif
├── GLiMCateNumberMapping.csv
├── glim_short2longname.txt

'''


def absolute_file_paths(directory):
    """

    Parameters
    ----------
    directory: 文件夹路径

    Returns
    -------
    list:
        文件夹及其子文件夹内所有文件的路径
    """

    def nest(nest_directory):
        for path, _, filenames in os.walk(nest_directory):
            for f in filenames:
                yield os.path.abspath(os.path.join(path, f))

    return list(nest(directory))


def shp_id(shpfile: str):
    '''

    :param shpfile: shapefile path e.g. ./0000.shp
    :return: shapefile id e.g. 0000
    '''
    return re.findall(r'[\d]+', shpfile)[-1]


def extract_raster(raster: str, shape_file: str, output_file=None, nodata=-9999):
    """ extract raster based on the given shapefile

    Parameters
    ----------
    shape_file: EPSG:4326 .shp 文件路径
    output_file: 输出 .tif 文件路径
    raster: EPSG:4326 .tif 文件路径
    nodata: 指定 nodata 的值
    """
    with fiona.open(shape_file, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
    with rasterio.open(raster) as src:
        out_image, out_transform = rasterio.mask.mask(src, shapes, nodata=nodata, crop=True)
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


class Glim():
    """
    基于 GliM 数据集，统计区域岩性比例
    """

    def __init__(self, glim_raster_tif: str, glim_cate_number_mapping_file: str, short2long_name_txt: str,
                 nan_value=65535):
        """
        glim_raster_tif: 转换后的 Glim 数据集（栅格）
        glim_cate_number_mapping_file: 包含 GLiM 栅格数值到岩性种类映射的 .csv 文件
        short2long_name_txt: 岩性种类短名称到长名称的映射, glim_short2longname.txt
        """
        self.glim_raster_tif = glim_raster_tif
        self.short2long_dataframe = pd.read_table(short2long_name_txt, sep=',')
        self.glim_mapping_dataframe = pd.read_table(glim_cate_number_mapping_file, sep=',')
        self.glim_mapping_dataframe['xx'] = [s[:2] for s in self.glim_mapping_dataframe['Litho']]
        self.nan_value = nan_value

    def glim_number2geol_mapping(self, value: int):
        return self.glim_mapping_dataframe[self.glim_mapping_dataframe['Value'] == value]['Litho'].values[0][:2]

    def glim_geol2number_mapping(self, geol: str):
        return self.glim_mapping_dataframe[self.glim_mapping_dataframe['xx'] == geol]['Value'].values

    def short2long_name(self, short_name: str):
        return self.short2long_dataframe[self.short2long_dataframe['short'] == short_name]['long'].values[0]

    def extract_basin_attributes_glim_all(self, shape_file: str) -> dict:
        """
        shape_file: shapefile 文件路径
        """
        res = extract_raster(raster=self.glim_raster_tif, shape_file=shape_file, output_file=None)
        res = res[res < 1000].flatten()
        res_list = res[res != self.nan_value].flatten().tolist()

        res_str = [self.glim_number2geol_mapping(number) for number in res_list]

        geol_class, count = np.unique(res_str, return_counts=True)

        res = {}
        for name, c in zip(geol_class, count):
            res[name] = c / np.sum(count)

        return res

    def extract_basin_attributes_glim(self, shape_file: str) -> dict:
        """
        shape_file: shapefile 文件路径
        """
        res = extract_raster(raster=self.glim_raster_tif, shape_file=shape_file, output_file=None)
        res = res[res < 1000].flatten()
        res_list = res[res != self.nan_value].flatten().tolist()

        res_str = [self.glim_number2geol_mapping(number) for number in res_list]

        geol_class, count = np.unique(res_str, return_counts=True)

        geol_class_rank = [x for _, x in sorted(zip(count, geol_class), reverse=True)]
        if len(geol_class_rank) == 0:
            return {'geol_class_1st: ': None,
                    'geol_class_1st_frac: ': None,
                    'geol_class_2nd: ': None,
                    'geol_class_2nd_frac: ': None,
                    'carb_rocks_frac: ': None}
        geol_class_1st = geol_class_rank[0]
        geol_class_1st_count = count[geol_class == geol_class_1st]
        geol_class_1st_frac = (geol_class_1st_count / np.sum(count))[0]
        if len(geol_class_rank) > 1:
            geol_class_2nd = geol_class_rank[1]
            geol_class_2nd_count = count[geol_class == geol_class_2nd]
            geol_class_2nd_frac = (geol_class_2nd_count / np.sum(count))[0]
        else:
            geol_class_2nd = None
            geol_class_2nd_frac = 0

        carb_rocks_count = count[geol_class == 'sc']
        if len(carb_rocks_count) == 0:
            carb_rocks_frac = 0
        else:
            carb_rocks_frac = (carb_rocks_count / np.sum(count))[0]

        return {'geol_class_1st: ': geol_class_1st,
                'geol_class_1st_frac: ': geol_class_1st_frac,
                'geol_class_2nd: ': geol_class_2nd,
                'geol_class_2nd_frac: ': geol_class_2nd_frac,
                'carb_rocks_frac: ': carb_rocks_frac}


if __name__ == '__main__':

    glim_raster_tif = "./GlimRaster.tif"
    glim_cate_number_mapping_file = "./GLiMCateNumberMapping.csv"
    short2long_name_txt = "./glim_short2longname.txt"
    nan_value = 65535

    glimer = Glim(glim_raster_tif=glim_raster_tif, glim_cate_number_mapping_file=glim_cate_number_mapping_file,
                  short2long_name_txt=short2long_name_txt, nan_value=nan_value)

    res = {}
    for shape_file in tqdm([file for file in absolute_file_paths('./shapefiles') if file.endswith('.shp')]):
        res[shp_id(shape_file)] = glimer.extract_basin_attributes_glim_all(shape_file=shape_file)
    pd.DataFrame(res).T.to_excel('./glim_result.xlsx')
