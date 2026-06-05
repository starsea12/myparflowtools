# ParFlow CONCN Share Platform

## 安装与使用

### 1. 克隆仓库

```
git clone https://github.com/ParFlowCommunity/ParFlow-CONCN-Share-Platform
cd ParFlow-CONCN-Share-Platform
```

### 2. 进入代码目录

```bash
cd concnshare
```

### 3. 创建 Conda 环境

```bash
conda env create -f environment.yaml
```

### 4. 激活环境

```bash
conda activate concnshare
```

### 5. （可选）自定义输出目录

默认输出目录为 `/ParFlow-CONCN-Share-Platform/outputs/`。如需更改，请设置环境变量：

```bash
export OUTPUT_DIR=/your/custom/path
```

### 6. 运行程序

```bash
run_two
```

按提示输入14位流域编码（如 `01010105000000`）即可开始处理。

## 输出文件

- `outputs/mask.tif`：二值掩膜 GeoTIFF
- `outputs/mask.pfb`：掩膜 PFB 文件
- `outputs/pos.json`：位置信息
- `outputs/<流域编码>.vtk` / `outputs/<流域编码>.pfsol`：域文件
- `outputs/slopex.<流域编码>.pfb` 等：裁剪后的 PFB 文件

## 环境变量

- `OUTPUT_DIR`：指定输出目录（默认为 `./outputs`）

## 注意事项

- 本工具仅支持 Linux 系统，需要预先安装 Conda。
- 确保对输入数据目录有读取权限。
- 若需生成 VTK/PFSOL，请确保 `pfmask-to-pfsol` 命令可用（已内置路径）。

## 问题反馈

请将问题提交至 GitHub Issues。
