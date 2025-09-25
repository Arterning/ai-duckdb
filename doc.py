import duckdb
import pandas as pd
import pyarrow.parquet as pq
from io import BytesIO
from google import genai
import duckdb
import hashlib
from dotenv import load_dotenv
import os

load_dotenv(override=True)

API_KEY=os.environ.get("GEMINI_API_KEY")


async def load_data_from_file(file_path: str):
    """根据文件类型加载数据到pandas DataFrame
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        tuple: (DataFrame, str) 数据和错误信息
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return None, "文件不存在"
        
    # 检查文件类型是否支持数据分析
    file_suffix = os.path.splitext(file_path)[1].lower()
    if file_suffix not in ['.parquet', '.csv', '.xlsx', '.xls', '.json']:
        return None, "文件类型不支持数据分析，仅支持 parquet、csv、xlsx、xls、json 文件"

    try:
        # 读取文件
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        # 根据文件类型加载数据到 pandas DataFrame
        df = None
        if file_suffix == '.parquet':
            buffer = BytesIO(file_bytes)
            table = pq.read_table(buffer)
            df = table.to_pandas()
        elif file_suffix == '.csv':
            df = pd.read_csv(BytesIO(file_bytes))
        elif file_suffix in ['.xlsx', '.xls']:
            engine = "openpyxl" if file_suffix == '.xlsx' else "xlrd"
            df = pd.read_excel(BytesIO(file_bytes), engine=engine)
        elif file_suffix == '.json':
            # 尝试不同的JSON读取方式
            try:
                # 先尝试按行读取（每行一个JSON对象）
                df = pd.read_json(BytesIO(file_bytes), lines=True)
            except:
                try:
                    # 再尝试作为JSON数组读取
                    df = pd.read_json(BytesIO(file_bytes))
                except:
                    # 最后尝试手动解析JSON
                    import json
                    text_content = file_bytes.decode('utf-8')
                    json_data = json.loads(text_content)

                    if isinstance(json_data, list):
                        df = pd.DataFrame(json_data)
                    elif isinstance(json_data, dict):
                        # 如果是字典，尝试将其转换为DataFrame
                        if all(isinstance(v, list) for v in json_data.values()):
                            # 如果所有值都是列表，作为列数据处理
                            df = pd.DataFrame(json_data)
                        else:
                            # 否则作为单行数据处理
                            df = pd.DataFrame([json_data])
                    else:
                        raise ValueError("不支持的JSON格式")
        
        if df is None or df.empty:
            return None, "无法读取文件数据或文件为空"
            
        return df, None
    except Exception as e:
        return None, f"文件加载失败: {str(e)}"


async def analyze_file(*, file_path: str):
    """分析文件并返回数据概要信息，同时将数据保存到DuckDB磁盘数据库

    Args:
        file_path (str): 文件路径

    Returns:
        dict: 包含数据概要信息的字典
    """
    try:
        # 加载数据
        df, error = await load_data_from_file(file_path)
        if error:
            return {
                "error": error
            }
            
        # 生成数据概要信息
        data_info = {
            "行数": len(df),
            "列数": len(df.columns),
            "列名": list(df.columns),
            "数据类型": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "前5行数据": df.head().to_dict('records')
        }
        
        # 生成唯一的数据库文件路径
        db_filename = f"data_{os.path.splitext(os.path.basename(file_path))[0]}.duckdb"
        db_path = os.path.join(os.path.dirname(file_path), db_filename)
        
        # 将数据保存到DuckDB磁盘数据库
        conn = duckdb.connect(db_path)
        conn.execute("CREATE OR REPLACE TABLE data_table AS SELECT * FROM df")
        conn.close()
        
        # 将数据库路径添加到返回结果中
        data_info["db_path"] = db_path
        
        return {
            "success": True,
            "data_info": data_info
        }
    except Exception as e:
        print(f"文件分析出错: {str(e)}")
        return {
            "error": f"文件分析出错: {str(e)}"
        }

async def analyze_data_with_ai(*, file_path: str, question: str, data_info: dict = None):
    """使用AI分析文件数据

    Args:
        file_path (str): 文件路径
        question (str): 用户问题
        data_info (dict): 可选，数据概要信息（包含db_path）

    Returns:
        dict: 包含分析结果的字典
    """
    # 如果没有提供data_info，则先分析文件获取数据概要和数据库路径
    if data_info is None:
        analyze_result = await analyze_file(file_path=file_path)
        if "error" in analyze_result:
            return analyze_result
        data_info = analyze_result["data_info"]
    
    # 检查data_info中是否包含数据库路径
    if "db_path" not in data_info:
        # 如果没有数据库路径，生成唯一的数据库文件路径
        db_filename = f"data_{os.path.splitext(os.path.basename(file_path))[0]}.duckdb"
        db_path = os.path.join(os.path.dirname(file_path), db_filename)
        data_info["db_path"] = db_path
        
        # 加载数据并保存到数据库
        df, error = await load_data_from_file(file_path)
        if error:
            return {
                "error": error
            }
            
        conn = duckdb.connect(db_path)
        conn.execute("CREATE OR REPLACE TABLE data_table AS SELECT * FROM df")
        conn.close()

    # 构建 AI 提示词
    file_name = os.path.basename(file_path)
    system_context = f"""你是一个数据分析专家。用户上传了一个名为"{file_name}"的数据文件，包含以下信息：

数据概要：
- 行数：{data_info['行数']}
- 列数：{data_info['列数']}
- 列名：{', '.join(data_info['列名'])}
- 数据类型：{data_info['数据类型']}

前5行数据示例：
{pd.DataFrame(data_info['前5行数据']).to_string()}

请根据用户的问题生成相应的SQL查询语句。注意：
1. 表名固定为 'data_table'
2. 只返回SQL语句，不要包含其他解释
3. SQL语句必须是DuckDB兼容的
4. 确保SQL语句是安全的，不包含删除、更新等操作
5. 如果问题不适合用SQL解决，请返回一个查询所有数据的SELECT语句"""

    user_input = f"用户问题：{question}"

    # 调用 Gemini API 生成 SQL
    try:
        # 初始化 Gemini
        client = genai.Client(api_key=API_KEY)

        # 生成 SQL
        prompt = f"{system_context}\n\n{user_input}"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        sql_query = response.text

    except Exception as e:
        return {
            "error": f"Gemini API 调用失败: {str(e)}"
        }

    if not sql_query:
        return {
            "error": "SQL查询生成失败"
        }
    
    # 清理SQL语句
    sql_query = sql_query.strip()
    if sql_query.startswith('```sql'):
        sql_query = sql_query[6:]
    if sql_query.endswith('```'):
        sql_query = sql_query[:-3]
    sql_query = sql_query.strip()
    
    # 使用DuckDB执行SQL查询，连接到磁盘数据库
    try:
        # 检查数据库路径是否存在
        db_path = data_info.get("db_path")
        if not db_path:
            return {
                "error": "数据库路径不存在"
            }
        
        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            return {
                "error": f"数据库文件不存在: {db_path}"
            }
            
        # 连接到数据库并执行查询
        conn = duckdb.connect(db_path)
        result = conn.execute(sql_query).fetchdf()
        conn.close()
        
    except Exception as e:
        return {
            "error": f"DuckDB查询执行失败: {str(e)}"
        }
    
    # 返回结果
    return {
        "question": question,
        "sql_query": sql_query,
        "data_info": data_info,
        "result": {
            "columns": list(result.columns),
            "data": result.to_dict('records'),
            "row_count": len(result)
        }
    }
