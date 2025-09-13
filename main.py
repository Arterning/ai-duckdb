import asyncio
from doc import analyze_data_with_ai


async def main():
    print("Hello from ai-duckdb!")

    # 示例：分析数据文件
    file_path = input("请输入数据文件路径: ")
    question = input("请输入您的问题: ")

    result = await analyze_data_with_ai(file_path=file_path, question=question)

    if "error" in result:
        print(f"错误: {result['error']}")
    else:
        print(f"\n问题: {result['question']}")
        print(f"生成的SQL: {result['sql_query']}")
        print(f"\n数据信息:")
        print(f"- 行数: {result['data_info']['行数']}")
        print(f"- 列数: {result['data_info']['列数']}")
        print(f"- 列名: {', '.join(result['data_info']['列名'])}")
        print(f"\n查询结果 ({result['result']['row_count']} 行):")
        for row in result['result']['data'][:5]:  # 显示前5行
            print(row)


if __name__ == "__main__":
    asyncio.run(main())
