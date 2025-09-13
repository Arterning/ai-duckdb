
## 效果
Hello from ai-duckdb!
请输入数据文件路径: sample_sales_data.csv
请输入您的问题: 销售业绩最好的是谁？

问题: 销售业绩最好的是谁？
生成的SQL: SELECT
  sales_rep,
  SUM(price * quantity) AS total_sales
FROM data_table
GROUP BY
  sales_rep
ORDER BY
  total_sales DESC
LIMIT 1;

数据信息:
- 行数: 40
- 列数: 11
- 列名: id, product_name, category, price, quantity, sale_date, customer_name, customer_age, customer_city, sales_rep, commission_rate

查询结果 (1 行):
{'sales_rep': '王红', 'total_sales': 7729.619999999998}