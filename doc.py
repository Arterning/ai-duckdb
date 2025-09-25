import duckdb
import pandas as pd
import pyarrow.parquet as pq
from io import BytesIO
from google import genai
from dotenv import load_dotenv
import os

load_dotenv(override=True)

API_KEY=os.environ.get("GEMINI_API_KEY")


async def analyze_data_with_ai(*, file_path: str, question: str):
    """使用AI分析文件数据

    Args:
        file_path (str): 文件路径
        question (str): 用户问题

    Returns:
        dict: 包含分析结果的字典
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return {
            "error": "文件不存在"
        }

    # 检查文件类型是否支持数据分析
    file_suffix = os.path.splitext(file_path)[1].lower()
    if file_suffix not in ['.parquet', '.csv', '.xlsx', '.xls', '.json']:
        return {
            "error": "文件类型不支持数据分析，仅支持 parquet、csv、xlsx、xls、json 文件"
        }

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
            return {
                "error": "无法读取文件数据或文件为空"
            }
        
        # 生成数据概要信息
        data_info = {
            "行数": len(df),
            "列数": len(df.columns),
            "列名": list(df.columns),
            "数据类型": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "前5行数据": df.head().to_dict('records')
        }
        
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
                "error": "AI生成SQL失败"
            }
        
        # 清理SQL语句
        sql_query = sql_query.strip()
        if sql_query.startswith('```sql'):
            sql_query = sql_query[6:]
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # 使用DuckDB执行SQL查询
        conn = duckdb.connect(':memory:')
        
        # 将DataFrame注册为表
        conn.register('data_table', df)
        
        # 执行SQL查询
        result = conn.execute(sql_query).fetchdf()
        
        # 关闭连接
        conn.close()
        
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
        
    except Exception as e:
        print(f"数据分析出错: {str(e)}")
        return {
            "error": f"数据分析出错: {str(e)}"
        }