# JD
一个关于 JD 分析的小的教学项目

## 项目依赖

本项目使用以下主要依赖：
- **pandas 2.3.3** - 数据分析和处理
- **numpy 2.2.6** - 数值计算
- **matplotlib 3.10.7** - 数据可视化
- **seaborn 0.13.2** - 高级数据可视化
- **jupyter** - 交互式数据分析环境
- **openpyxl 3.1.5** - Excel 文件读写

## 项目结构

```
JD/
├── datas/
│   └── src/
│       └── 招聘数据总表_2510.xlsx    # 原始数据文件
├── 01_数据探索分析.ipynb              # 探索性数据分析 Notebook
├── requirements.txt                   # Python 依赖包列表
├── .gitignore                        # Git 忽略文件配置
└── README.md                         # 项目说明文档
```

## 环境设置

### 创建虚拟环境

为了保持项目依赖的独立性，建议使用虚拟环境。

#### 1. 创建虚拟环境

```bash
python3 -m venv venv
```

#### 2. 激活虚拟环境

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

#### 3. 安装依赖（如果有 requirements.txt）

```bash
pip install -r requirements.txt
```

#### 4. 退出虚拟环境

```bash
deactivate
```

## 快速开始

### 启动 Jupyter Notebook

激活虚拟环境后，启动 Jupyter Notebook：

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动 Jupyter Notebook
jupyter notebook
```

浏览器会自动打开，然后可以打开 `01_数据探索分析.ipynb` 开始分析。

### 使用 Python 脚本

也可以直接编写 Python 脚本进行数据分析：

```python
import pandas as pd

# 读取数据
df = pd.read_excel('datas/src/招聘数据总表_2510.xlsx')

# 数据分析示例
print(df.head())
print(df.describe())
```

## 注意事项

- 虚拟环境文件夹 `venv/` 已被添加到 `.gitignore`，不会被提交到版本控制系统
- 每次开始工作前，请记得激活虚拟环境
- 安装新的包后，请更新 `requirements.txt` 文件：
  ```bash
  pip freeze > requirements.txt
  ```
