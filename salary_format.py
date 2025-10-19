"""
薪资清洗工具
支持格式：
- 1.2-18k
- 3.8-4.2k13薪
- 3k及以下
- 100-150元/天
- 6k-8500元/月
- 6500-8k元/月
- 5500-6500元/月
"""

import pandas as pd
import re
import os

def clean_salary(text):
    """
    清洗并标准化薪资字符串
    返回字典：raw_salary, min_monthly, max_monthly, annual_months, total_min, total_max, salary_type, parse_flag
    """
    if pd.isna(text) or not str(text).strip():
        return {
            'raw_salary': str(text),
            'min_monthly': None,
            'max_monthly': None,
            'annual_months': 12,
            'total_min': None,
            'total_max': None,
            'salary_type': '空值',
            'parse_flag': '原始为空'
        }

    raw = str(text).strip()
    parse_flag = []
    salary_type = '月薪'
    annual_months = 12
    min_val = None
    max_val = None

    # --- Step 1: 统一预处理 ---
    text = raw.lower().strip()
    text = re.sub(r'\s+', '', text)           # 去空格
    text = re.sub(r'[·•]', '', text)          # 去·
    text = re.sub(r'[—–\-]', '-', text)       # 统一横线
    parse_flag.append('预处理')

    # --- Step 2: 处理“Xk及以下” ---
    if '及以下' in raw:
        match = re.search(r'(\d+\.?\d*)[kK]?', raw)
        if match:
            max_val = float(match.group(1))
            min_val = 0
            salary_type = '上限型'
            parse_flag.append('及以下转0-max')
            months_match = re.search(r'(\d+)薪', raw)
            if months_match:
                annual_months = int(months_match.group(1))
                parse_flag.append('提取薪数')
            return {
                'raw_salary': raw,
                'min_monthly': min_val,
                'max_monthly': max_val,
                'annual_months': annual_months,
                'total_min': round(min_val * annual_months, 2),
                'total_max': round(max_val * annual_months, 2),
                'salary_type': salary_type,
                'parse_flag': '|'.join(parse_flag)
            }

    # --- Step 3: 处理“万”单位 ---
    if '万' in text:
        def wan_replace(m):
            num = float(m.group(1))
            parse_flag.append('万转k')
            return str(num * 10) + 'k'
        text = re.sub(r'(\d+\.?\d*)万', wan_replace, text)

    # --- Step 4: 处理“元/天” ---
    day_match = re.search(r'(\d+)-(\d+)元/天', text)
    if day_match:
        min_day = int(day_match.group(1))
        max_day = int(day_match.group(2))
        min_val = round(min_day * 30 / 1000, 1)  # 转为k
        max_val = round(max_day * 30 / 1000, 1)
        salary_type = '日薪换算'
        parse_flag.append('元/天转月薪')
        months_match = re.search(r'(\d+)薪', text)
        if months_match:
            annual_months = int(months_match.group(1))
            parse_flag.append('提取薪数')
        text = f"{min_val}k-{max_val}k"
        parse_flag.append('构造标准文本')

    # --- Step 5: 处理“元/月”（支持混合格式）---
    if '元/月' in text:
        parse_flag.append('处理元/月')
        months_match = re.search(r'(\d+)薪', text)
        if months_match:
            annual_months = int(months_match.group(1))
            text = re.sub(r'\d+薪', '', text)
            parse_flag.append('提取薪数')

        # 情况1: 6500-8k元/月 或 6k-8500元/月
        match_mixed = re.search(r'(\d+)-([0-9.]+)k元/月', text) or re.search(r'([0-9.]+)k-(\d+)元/月', text)
        if match_mixed:
            a, b = match_mixed.group(1), match_mixed.group(2)
            if a.isdigit():  # a是数字，b是k
                min_val = round(int(a) / 1000, 1)
                max_val = float(b)
            else:  # a是k，b是数字
                min_val = float(a)
                max_val = round(int(b) / 1000, 1)
            if min_val > max_val:
                min_val, max_val = max_val, min_val
            parse_flag.append('混合型元/月转k')
            text = f"{min_val}k-{max_val}k"

        # 情况2: 5500-6500元/月
        range_match = re.search(r'(\d+)-(\d+)元/月', text)
        if range_match:
            min_val = round(int(range_match.group(1)) / 1000, 1)
            max_val = round(int(range_match.group(2)) / 1000, 1)
            if min_val > max_val:
                min_val, max_val = max_val, min_val
            parse_flag.append('元/月范围转k')
            text = f"{min_val}k-{max_val}k"

        # 情况3: 单值 6500元/月
        single_match = re.search(r'(\d+)元/月', text)
        if single_match:
            val = round(int(single_match.group(1)) / 1000, 1)
            parse_flag.append('元/月单值转k')
            text = f"{val}k"

    # --- Step 6: 补全缺失的 k ---
    text = re.sub(r'(\d+\.?\d*)-(\d+[kK])', lambda m: m.group(1) + 'k-' + m.group(2), text)
    parse_flag.append('补全前项k')
    text = re.sub(r'([kK])(\d+\.?\d*)\b(?![kK])', lambda m: m.group(1) + m.group(2) + 'k', text)
    parse_flag.append('补全后项k')

    # --- Step 7: 数字转k（5000 → 5k）---
    def num_replace(m):
        num = int(m.group(1))
        parse_flag.append('数字转k')
        return f"{num / 1000:.1f}k"
    text = re.sub(r'\b(\d{4,})\b(?=[^-]*[kK])', num_replace, text)

    # --- Step 8: 修复小数点错误（2.20K → 22K）---
    def fix_decimal(m):
        num_str = m.group(1)
        num = float(num_str)
        if num < 10 and '.' in num_str and len(num_str.split('.')[-1]) == 2:
            parse_flag.append('小数点修正')
            return str(int(num * 10)) + 'k'
        return num_str + 'k'
    text = re.sub(r'(\d+\.\d{2})[kK]', fix_decimal, text)

    # --- Step 9: 提取年薪月数 ---
    months_match = re.search(r'k(\d+)薪', text, re.I)
    if months_match:
        annual_months = int(months_match.group(1))
        text = re.sub(r'k\d+薪', 'k', text)
        parse_flag.append('提取k后薪数')

    dot_match = re.search(r'·(\d+)薪', text)
    if dot_match:
        annual_months = int(dot_match.group(1))
        text = re.sub(r'·\d+薪', '', text)
        parse_flag.append('提取·薪数')

    # --- Step 10: 解析主结构 ---
    pattern = r'([0-9.]+)[kK]?-([0-9.]+)[kK]?'
    match = re.search(pattern, text)
    if match:
        min_val = float(match.group(1))
        max_val = float(match.group(2))
        parse_flag.append('正常解析')
    else:
        single_match = re.search(r'([0-9.]+)[kK]', text)
        if single_match:
            val = float(single_match.group(1))
            min_val = max_val = val
            parse_flag.append('单值解析')
        else:
            return {
                'raw_salary': raw,
                'min_monthly': None, 'max_monthly': None, 'annual_months': 12,
                'total_min': None, 'total_max': None,
                'salary_type': '未解析',
                'parse_flag': '最终无匹配|' + raw
            }

    # --- Step 11: 修正倒挂 ---
    if min_val > max_val:
        min_val, max_val = max_val, min_val
        parse_flag.append('倒挂修正')

    # --- Step 12: 计算年薪 ---
    total_min = round(min_val * annual_months, 2)
    total_max = round(max_val * annual_months, 2)

    return {
        'raw_salary': raw,
        'min_monthly': min_val,
        'max_monthly': max_val,
        'annual_months': annual_months,
        'total_min': total_min,
        'total_max': total_max,
        'salary_type': salary_type,
        'parse_flag': '|'.join(parse_flag)
    }

# ==================== 主程序 ====================
if __name__ == "__main__":
    # 📁 请将你的 Excel 文件放在此脚本同目录下，并命名为 'salary_format.xlsx'
    file_path = 'salary_format.xlsx'

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在：{file_path}")
        print("请将文件命名为 'salary_format.xlsx' 并放在与脚本相同目录。")
        exit(1)

    try:
        df = pd.read_excel(file_path, sheet_name=0, dtype=str)
        print(f"✅ 成功读取文件：{file_path}，共 {len(df)} 行数据")

        # 自动识别薪资列
        salary_col = None
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['薪', '工资', '薪资', 'pay', 'salary']):
                salary_col = col
                break

        if not salary_col:
            print("❌ 未找到薪资相关列名，请检查列名是否包含 '薪'、'工资' 等关键词。")
            print(f"当前列名：{list(df.columns)}")
            exit(1)

        print(f"📊 检测到薪资列：'{salary_col}'")

        # 清洗数据
        print("🔄 正在清洗薪资数据...")
        results = df[salary_col].apply(clean_salary)
        result_df = pd.DataFrame(list(results))

        # 重排列顺序
        result_df = result_df[[
            'raw_salary', 'min_monthly', 'max_monthly', 'annual_months',
            'total_min', 'total_max', 'salary_type', 'parse_flag'
        ]]

        # 保存结果
        output_path = 'cleaned_salary.csv'
        result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ 清洗完成！共处理 {len(df)} 条数据")
        print(f"📁 已保存至：{output_path}")

        # 显示前5行示例
        print("\n📋 清洗结果前5行示例：")
        print(result_df.head().to_string(index=False))

        # 显示解析失败的条目
        failed = result_df[result_df['parse_flag'].str.contains('未解析|异常|最终无匹配')]
        if len(failed) > 0:
            print(f"\n⚠️  注意：有 {len(failed)} 条数据未成功解析：")
            print(failed[['raw_salary', 'parse_flag']].to_string(index=False))

    except Exception as e:
        print(f"❌ 处理过程中发生错误：{e}")
        import traceback
        traceback.print_exc()