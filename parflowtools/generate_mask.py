#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
程序一：生成流域掩膜 TIF 及位置信息
支持命令行调用和函数导入
"""

import numpy as np
import rasterio
from rasterio import features
import geopandas as gpd
import json
import argparse


def generate_mask(shp_path, code, field, tif_path, out_mask_path, out_json_path, expand=1, verbose=True):
    """
    生成流域掩膜 TIF 及位置信息
    
    参数:
        shp_path: Shapefile 路径
        code: 流域编码（如 '01010105000000'）
        field: 存储编码的字段名
        tif_path: 模板 GeoTIFF（与 PFB 完全对齐）
        out_mask_path: 输出掩膜 TIF 路径
        out_json_path: 输出位置 JSON 文件路径
        expand: 向外扩展的像素数，默认1
        verbose: 是否打印详细信息，默认 True
    
    返回:
        dict: 位置信息 {'row_min': int, 'col_min': int, 'height': int, 'width': int}
    """
    def log(msg):
        if verbose:
            print(f"[程序一] {msg}")
    
    # 1. 读取流域几何
    gdf = gpd.read_file(shp_path)
    basin = gdf[gdf[field] == code]
    if basin.empty:
        raise ValueError(f"未找到编码 {code} 的记录")
    geom = basin.geometry.unary_union if len(basin) > 1 else basin.geometry.iloc[0]
    shp_crs = gdf.crs

    # 2. 利用模板 TIF 生成掩膜
    with rasterio.open(tif_path) as src:
        # 投影几何到模板的 CRS
        gdf_geom = gpd.GeoDataFrame(geometry=[geom], crs=shp_crs)
        geom_proj = gdf_geom.to_crs(src.crs).geometry.iloc[0]

        # 计算扩展后的地理边界
        xmin, ymin, xmax, ymax = geom_proj.bounds
        px_w = abs(src.transform.a)
        px_h = abs(src.transform.e)
        new_xmin = xmin - expand * px_w
        new_xmax = xmax + expand * px_w
        new_ymin = ymin - expand * px_h
        new_ymax = ymax + expand * px_h

        # 计算输出栅格尺寸和仿射变换
        width = int(round((new_xmax - new_xmin) / px_w))
        height = int(round((new_ymax - new_ymin) / px_h))
        out_transform = rasterio.Affine(px_w, 0.0, new_xmin, 0.0, -px_h, new_ymax)

        # 生成二值掩膜（True=内部）
        mask_bool = features.geometry_mask(
            [geom_proj], out_shape=(height, width),
            transform=out_transform, invert=False, all_touched=False
        )
        # 内部0，外部1（与常见相反，但后续裁剪程序会适配）
        mask_uint8 = np.where(mask_bool, 0, 1).astype(np.uint8)

        # 写入掩膜 TIF
        profile = src.profile
        profile.update({
            "driver": "GTiff", "height": height, "width": width,
            "transform": out_transform, "dtype": rasterio.uint8,
            "count": 1, "compress": "lzw", "nodata": None
        })
        with rasterio.open(out_mask_path, "w", **profile) as dst:
            dst.write(mask_uint8, 1)
        log(f"掩膜已保存: {out_mask_path}")

        # 计算掩膜矩形在原始 TIF 中的行列偏移
        col_min, row_min = ~src.transform * (new_xmin, new_ymax)
        col_min = int(round(col_min))
        row_min = int(round(row_min))
        if col_min < 0 or row_min < 0:
            raise ValueError("掩膜矩形超出模板 TIF 范围，请减小 --expand 或检查几何范围")

        pos_info = {
            "row_min": row_min,
            "col_min": col_min,
            "height": height,
            "width": width
        }
        with open(out_json_path, "w") as f:
            json.dump(pos_info, f, indent=2)
        log(f"位置信息已保存: {out_json_path}")
        log(f"起始行列 (row, col) = ({row_min}, {col_min}), 尺寸 = {height} x {width}")
        
        return pos_info


def main():
    parser = argparse.ArgumentParser(description="生成流域掩膜 TIF 及位置信息")
    parser.add_argument("--shp", required=True, help="Shapefile 路径")
    parser.add_argument("--code", required=True, help="流域编码（如 '123456'）")
    parser.add_argument("--field", default="PFBAS", help="存储编码的字段名，默认 PFBAS")
    parser.add_argument("--tif", required=True, help="与 PFB 完全对齐的模板 GeoTIFF")
    parser.add_argument("--out_mask", required=True, help="输出掩膜 TIF 路径")
    parser.add_argument("--out_json", required=True, help="输出位置 JSON 文件路径")
    parser.add_argument("--expand", type=int, default=1, help="向外扩展的像素数，默认1")
    args = parser.parse_args()

    generate_mask(
        shp_path=args.shp,
        code=args.code,
        field=args.field,
        tif_path=args.tif,
        out_mask_path=args.out_mask,
        out_json_path=args.out_json,
        expand=args.expand,
        verbose=True
    )


if __name__ == "__main__":
    main()