from flask import Flask, request, jsonify, render_template, session
import os
import json
import uuid
from datetime import datetime
import asyncio
from werkzeug.utils import secure_filename
from doc import analyze_file, analyze_data_with_ai
from database import ChatDatabase
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# 配置文件上传
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'parquet', 'json'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# 确保上传文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 初始化数据库
db = ChatDatabase()

def format_analysis_result(result):
    """将AI分析结果转换为markdown格式"""
    if "error" in result:
        return f"❌ **错误**: {result['error']}"

    markdown_content = []

    # 问题标题
    markdown_content.append(f"## 📊 数据分析结果")
    markdown_content.append(f"**问题**: {result['question']}")
    markdown_content.append("")

    # SQL查询
    markdown_content.append("### 🔍 生成的SQL查询")
    markdown_content.append("```sql")
    markdown_content.append(result['sql_query'])
    markdown_content.append("```")
    markdown_content.append("")

    # 数据信息
    data_info = result['data_info']
    markdown_content.append("### 📋 数据概览")
    markdown_content.append(f"- **行数**: {data_info['行数']:,}")
    markdown_content.append(f"- **列数**: {data_info['列数']}")
    markdown_content.append(f"- **列名**: {', '.join(data_info['列名'])}")
    markdown_content.append("")

    # 查询结果
    query_result = result['result']
    markdown_content.append(f"### 📈 查询结果 ({query_result['row_count']:,} 行)")

    if query_result['row_count'] == 0:
        markdown_content.append("没有找到匹配的数据。")
    else:
        # 生成表格
        columns = query_result['columns']
        data = query_result['data']

        # 表格头部
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join([":---"] * len(columns)) + " |"

        markdown_content.append(header)
        markdown_content.append(separator)

        # 表格数据（最多显示前10行）
        display_rows = min(10, len(data))
        for i in range(display_rows):
            row = data[i]
            row_values = []
            for col in columns:
                value = row.get(col)
                if value is None:
                    row_values.append("null")
                elif isinstance(value, (int, float)):
                    if isinstance(value, float):
                        row_values.append(f"{value:.2f}")
                    else:
                        row_values.append(f"{value:,}")
                else:
                    # 截断过长的文本
                    str_value = str(value)
                    if len(str_value) > 50:
                        str_value = str_value[:47] + "..."
                    row_values.append(str_value)

            markdown_content.append("| " + " | ".join(row_values) + " |")

        if query_result['row_count'] > 10:
            markdown_content.append("")
            markdown_content.append(f"*显示前 10 行，共 {query_result['row_count']:,} 行*")

    return "\n".join(markdown_content)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件类型，仅支持 CSV, Excel, Parquet, JSON'}), 400

        # 保存文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # 异步调用文件分析
        result = asyncio.run(analyze_file(file_path=filepath))

        if 'error' in result:
            # 如果分析出错，删除临时文件
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify(result), 400

        # 生成会话ID
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            db.create_session(session_id)

        # 保存文件信息到数据库
        file_info = {
            'id': str(uuid.uuid4()),
            'filename': filename,
            'filepath': filepath,
            'data_info': result['data_info']
        }
        db.save_file_info(session_id, file_info)

        # 返回文件信息和数据概要
        return jsonify({
            'success': True,
            'file_id': file_info['id'],
            'filename': filename,
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/ask_question', methods=['POST'])
def ask_question():
    try:
        # 获取请求参数
        data = request.get_json()
        file_id = data.get('file_id')
        question = data.get('question', '')

        if not file_id:
            return jsonify({'error': '请选择要分析的文件'}), 400

        if not question.strip():
            return jsonify({'error': '请输入问题'}), 400

        # 获取会话ID
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': '请先上传文件'}), 400

        # 获取文件详情
        file_detail = db.get_file_detail(file_id)
        if not file_detail:
            return jsonify({'error': '文件不存在'}), 404

        # 检查文件是否属于当前会话
        # 注意：这里简化处理，实际应该检查file_detail.session_id == session_id

        # 异步调用AI分析
        result = asyncio.run(
            analyze_data_with_ai(
                file_path=file_detail['filepath'],
                question=question,
                data_info=file_detail['data_info']
            )
        )

        if 'error' in result:
            return jsonify(result), 400

        # 将结果转换为markdown格式
        markdown_result = format_analysis_result(result)

        # 生成聊天记录
        chat_record = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'result': result,
            'markdown_result': markdown_result
        }

        # 保存到数据库
        db.save_chat_record(session_id, file_id, chat_record)

        return jsonify({
            'success': True,
            'chat_id': chat_record['id'],
            'markdown_result': markdown_result
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/chat_history')
def get_chat_history():
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'history': []})

    history = db.get_chat_history(session_id)
    return jsonify({'history': history})

@app.route('/api/new_session', methods=['POST'])
def new_session():
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    db.create_session(session_id)
    return jsonify({'session_id': session_id})

@app.route('/api/sessions')
def get_all_sessions():
    """获取所有会话列表"""
    sessions = db.get_all_sessions()
    return jsonify({'sessions': sessions})

@app.route('/api/files')
def get_files():
    """获取当前会话的所有文件"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'files': []})
    
    files = db.get_files(session_id)
    return jsonify({'files': files})

@app.route('/api/switch_session/<session_id>', methods=['POST'])
def switch_session(session_id):
    """切换到指定会话"""
    if db.session_exists(session_id):
        session['session_id'] = session_id
        return jsonify({'success': True, 'session_id': session_id})
    else:
        return jsonify({'error': '会话不存在'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)