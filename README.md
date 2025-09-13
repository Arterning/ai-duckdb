# AI-DuckDB 智能数据分析工具

## 📊 项目简介

AI-DuckDB 是一个基于人工智能的数据分析工具，结合了 DuckDB 的强大 SQL 引擎和 Google Gemini AI 的自然语言处理能力。用户只需用自然语言提出问题，系统就能自动生成相应的 SQL 查询语句并执行分析。

## ✨ 核心特性

- 🤖 **AI 驱动**: 使用 Google Gemini API 将自然语言转换为 SQL 查询
- 🚀 **高性能**: 基于 DuckDB 内存数据库，查询速度极快
- 📁 **多格式支持**: 支持 CSV、Excel (.xlsx, .xls)、Parquet 文件格式
- 🌐 **中文友好**: 完全支持中文问答和数据分析
- 🔒 **安全可靠**: 自动过滤危险 SQL 操作，确保数据安全
- 📈 **直观输出**: 结构化显示查询结果和数据统计信息

## 🏗️ 技术架构

```
用户自然语言问题 → Gemini API → SQL查询 → DuckDB执行 → 结构化结果
```

### 核心依赖
- **DuckDB**: 高性能分析型数据库
- **Google Generative AI**: 自然语言处理
- **Pandas**: 数据处理和转换
- **PyArrow**: Parquet 文件支持

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install duckdb pandas pyarrow google-generativeai openpyxl xlrd
```

### 2. 配置环境变量

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

或在 Windows 中：
```cmd
set GEMINI_API_KEY=your-gemini-api-key-here
```

### 3. 运行程序

```bash
python main.py
```

### 4. 使用示例

```
Hello from ai-duckdb!
请输入数据文件路径: sample_sales_data.csv
请输入您的问题: 销售业绩最好的是谁？

问题: 销售业绩最好的是谁？
生成的SQL: SELECT sales_rep, SUM(price * quantity) AS total_sales
           FROM data_table GROUP BY sales_rep ORDER BY total_sales DESC LIMIT 1;

数据信息:
- 行数: 40
- 列数: 11
- 列名: id, product_name, category, price, quantity, sale_date, customer_name, customer_age, customer_city, sales_rep, commission_rate

查询结果 (1 行):
{'sales_rep': '王红', 'total_sales': 7729.62}
```

## 📁 项目结构

```
ai-duckdb/
├── README.md                  # 项目说明文档
├── main.py                    # 主程序入口
├── doc.py                     # 核心数据分析模块
├── sample_sales_data.csv      # 示例数据文件
├── pyproject.toml            # 项目配置
└── uv.lock                   # 依赖锁定文件
```

## 🎯 支持的查询类型

- 📈 **统计分析**: 求和、平均值、最大/最小值
- 🔍 **数据筛选**: 按条件过滤数据
- 📊 **分组聚合**: 按类别统计分析
- 📅 **时间分析**: 时间序列和趋势分析
- 🏆 **排名分析**: Top N 查询
- 🔗 **关联分析**: 多维度数据关联

## 🗺️ 发展路线图 (Roadmap)

### 🎯 v1.0 (当前版本)
- [x] 基础 AI 查询功能
- [x] 多文件格式支持
- [x] 命令行界面

### 🚀 v1.1 (短期目标 - 3个月内)
- [ ] **Web 界面**: 开发 Web 界面
- [ ] **可视化图表**: 集成 ECharts/Chart.js 自动生成图表
- [ ] **查询历史**: 保存和管理历史查询记录
- [ ] **数据源扩展**: 支持 JSON、XML 格式
- [ ] **批量分析**: 支持多文件同时分析

### 🔥 v1.2 (中期目标 - 6个月内)
- [ ] **数据库连接**: 支持 PostgreSQL、MySQL、SQLite
- [ ] **实时数据**: 支持 Kafka、Redis 等实时数据源
- [ ] **AI 模型选择**: 支持多种 AI 模型 (OpenAI GPT、Claude 等)
- [ ] **自定义函数**: 支持用户定义 SQL 函数
- [ ] **数据清洗**: AI 辅助数据质量检查和清洗

### 🌟 v2.0 (长期愿景 - 1年内)
- [ ] **机器学习集成**: 自动预测和异常检测
- [ ] **自然语言报告**: AI 自动生成数据分析报告
- [ ] **协作功能**: 多用户协作和权限管理
- [ ] **插件系统**: 可扩展的插件架构
- [ ] **移动端支持**: iOS/Android 移动应用


### 🎯 竞争优势
1. **本地部署**: 数据不离开本地环境，保障隐私安全
2. **中文优化**: 专门针对中文用户优化，理解更准确
3. **轻量高效**: 基于 DuckDB，性能优异且部署简单
4. **开源免费**: 完全开源，可自由定制和扩展

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送分支: `git push origin feature/AmazingFeature`
5. 提交 Pull Request

## 📄 开源协议

本项目采用 MIT 协议开源。详见 [LICENSE](LICENSE) 文件。

## 💬 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 讨论交流: [GitHub Discussions]

---

⭐ 如果这个项目对你有帮助，欢迎点个 Star！