# crop_pfb.py 修正版
import numpy as np
import rasterio
from parflow.tools.io import read_pfb, write_pfb
import json
import argparse

def crop_pfb(pfb_path, mask_path, pos_json_path, out_pfb_path, verbose=True):
    def log(msg):
        if verbose:
            print(f"[程序二] {msg}")
    
    with open(pos_json_path, "r") as f:
        pos = json.load(f)
    row_min = pos["row_min"]
    col_min = pos["col_min"]
    height = pos["height"]
    width = pos["width"]
    log(f"位置信息: 起始行={row_min}, 起始列={col_min}, 尺寸={height}x{width}")

    with rasterio.open(mask_path) as src:
        mask = src.read(1)
        mask = (mask > 0).astype(np.uint8)
    if mask.shape != (height, width):
        log(f"警告：掩膜实际尺寸 {mask.shape} 与 JSON 不一致，将以掩膜为准")
        height, width = mask.shape

    log(f"读取 PFB: {pfb_path}")
    pfb = read_pfb(pfb_path)      # (Z, Y_nat, X_nat), Y 从南到北
    z, ny, nx = pfb.shape
    log(f"PFB 原始形状: {pfb.shape}")

    pfb_flipped = np.flip(pfb, axis=1)   # 现在 Y 从北到南

    if row_min + height > pfb_flipped.shape[1] or col_min + width > pfb_flipped.shape[2]:
        raise ValueError("裁剪区域超出 PFB 范围")
    pfb_cropped = pfb_flipped[:, row_min:row_min+height, col_min:col_min+width]
    log(f"裁剪后子区域形状: {pfb_cropped.shape}")

    mask_3d = mask[np.newaxis, :, :]   # (1, H, W)
    pfb_masked = pfb_cropped * mask_3d

    pfb_result = np.flip(pfb_masked, axis=1)

    # 确保输出为 float64
    pfb_result = pfb_result.astype(np.float64, copy=False)
    write_pfb(out_pfb_path, pfb_result,dx=961.72,dy=961.72,dz=200,dist=False)
    log(f"裁剪后 PFB 已保存: {out_pfb_path}")
    log(f"输出形状: {pfb_result.shape}")
    log(f"非零像素数（流域内）: {np.sum(pfb_result != 0)}")
    return pfb_result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pfb", required=True)
    parser.add_argument("--mask", required=True)
    parser.add_argument("--pos_json", required=True)
    parser.add_argument("--out_pfb", required=True)
    args = parser.parse_args()
    crop_pfb(args.pfb, args.mask, args.pos_json, args.out_pfb, verbose=True)

if __name__ == "__main__":
    main()