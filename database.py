import sqlite3
import json
from datetime import datetime
import os
import duckdb

class ChatDatabase:
    def __init__(self, db_path='chat_history.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建文件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                filename TEXT,
                filepath TEXT,
                data_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')

        # 创建聊天记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_records (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                file_id TEXT,
                timestamp TIMESTAMP,
                question TEXT,
                result TEXT,
                markdown_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        ''')

        conn.commit()
        conn.close()

    def create_session(self, session_id):
        """创建新会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO sessions (id, created_at, updated_at)
            VALUES (?, ?, ?)
        ''', (session_id, datetime.now(), datetime.now()))

        conn.commit()
        conn.close()

    def save_file_info(self, session_id, file_info):
        """保存文件信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 确保会话存在
        cursor.execute('SELECT id FROM sessions WHERE id = ?', (session_id,))
        if not cursor.fetchone():
            self.create_session(session_id)

        # 保存文件信息
        cursor.execute('''
            INSERT INTO files
            (id, session_id, filename, filepath, data_info)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            file_info['id'],
            session_id,
            file_info['filename'],
            file_info['filepath'],
            json.dumps(file_info['data_info'], ensure_ascii=False)
        ))

        # 更新会话的最后更新时间
        cursor.execute('''
            UPDATE sessions SET updated_at = ? WHERE id = ?
        ''', (datetime.now(), session_id))

        conn.commit()
        conn.close()

    def get_files(self, session_id):
        """获取指定会话的所有文件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, filename, created_at
            FROM files
            WHERE session_id = ?
            ORDER BY created_at DESC
        ''', (session_id,))

        files = []
        for row in cursor.fetchall():
            file = {
                'id': row[0],
                'filename': row[1],
                'created_at': row[2]
            }
            files.append(file)

        conn.close()
        return files

    def get_file_detail(self, file_id):
        """获取文件详情"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, filename, filepath, data_info
            FROM files
            WHERE id = ?
        ''', (file_id,))

        row = cursor.fetchone()
        if not row:
            return None

        file_detail = {
            'id': row[0],
            'filename': row[1],
            'filepath': row[2],
            'data_info': json.loads(row[3]) if row[3] else {}
        }

        conn.close()
        return file_detail

    def save_chat_record(self, session_id, file_id, chat_record):
        """保存聊天记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 确保会话存在
        cursor.execute('SELECT id FROM sessions WHERE id = ?', (session_id,))
        if not cursor.fetchone():
            self.create_session(session_id)

        # 保存聊天记录
        cursor.execute('''
            INSERT INTO chat_records
            (id, session_id, file_id, timestamp, question, result, markdown_result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            chat_record['id'],
            session_id,
            file_id,
            chat_record['timestamp'],
            chat_record['question'],
            json.dumps(chat_record['result'], ensure_ascii=False),
            chat_record['markdown_result']
        ))

        # 更新会话的最后更新时间
        cursor.execute('''
            UPDATE sessions SET updated_at = ? WHERE id = ?
        ''', (datetime.now(), session_id))

        conn.commit()
        conn.close()

    def get_chat_history(self, session_id):
        """获取指定会话的聊天历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT cr.id, cr.timestamp, cr.question, f.filename, cr.result, cr.markdown_result
            FROM chat_records cr
            LEFT JOIN files f ON cr.file_id = f.id
            WHERE cr.session_id = ?
            ORDER BY cr.timestamp ASC
        ''', (session_id,))

        records = []
        for row in cursor.fetchall():
            record = {
                'id': row[0],
                'timestamp': row[1],
                'question': row[2],
                'filename': row[3],
                'result': json.loads(row[4]) if row[4] else {},
                'markdown_result': row[5]
            }
            records.append(record)

        conn.close()
        return records

    def get_all_sessions(self):
        """获取所有会话的基本信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT s.id, s.created_at, s.updated_at,
                   COUNT(cr.id) as chat_count,
                   cr.question as latest_question,
                   cr.filename as latest_filename
            FROM sessions s
            LEFT JOIN chat_records cr ON s.id = cr.session_id
            LEFT JOIN (
                SELECT session_id, MAX(timestamp) as max_timestamp
                FROM chat_records
                GROUP BY session_id
            ) latest ON s.id = latest.session_id AND cr.timestamp = latest.max_timestamp
            GROUP BY s.id, s.created_at, s.updated_at, cr.question, cr.filename
            ORDER BY s.updated_at DESC
        ''', ())

        sessions = []
        for row in cursor.fetchall():
            session = {
                'id': row[0],
                'created_at': row[1],
                'updated_at': row[2],
                'chat_count': row[3],
                'latest_question': row[4],
                'latest_filename': row[5]
            }
            sessions.append(session)

        conn.close()
        return sessions

    def delete_session(self, session_id):
        """删除会话及其所有聊天记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM chat_records WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))

        conn.commit()
        conn.close()

    def session_exists(self, session_id):
        """检查会话是否存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM sessions WHERE id = ?', (session_id,))
        exists = cursor.fetchone() is not None

        conn.close()
        return exists