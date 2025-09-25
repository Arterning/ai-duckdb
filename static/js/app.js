$(document).ready(function() {
    let selectedFile = null;
    let chatHistory = [];
    let allSessions = [];
    let currentSessionId = null;

    // 初始化
    init();

    function init() {
        loadAllSessions();
        loadChatHistory();
        loadFilesList();
        setupEventHandlers();
    }

    // 设置事件处理器
    function setupEventHandlers() {
        // 文件上传相关
        $('#dragArea').on('click', function(e) {
            $('#fileInput')[0].click();
        });

        $('#fileInput').on('change', function(e) {
            handleFileSelect(e.target.files[0]);
        });

        // 拖拽功能
        $('#dragArea').on('dragover', function(e) {
            e.preventDefault();
            $(this).addClass('drag-over');
        });

        $('#dragArea').on('dragleave', function(e) {
            e.preventDefault();
            $(this).removeClass('drag-over');
        });

        $('#dragArea').on('drop', function(e) {
            e.preventDefault();
            $(this).removeClass('drag-over');
            const files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });

        // 移除文件
        $('#removeFile').on('click', function(e) {
            e.stopPropagation();
            removeFile();
        });

        // 表单提交
        $('#uploadForm').on('submit', function(e) {
            e.preventDefault();
            submitAnalysis();
        });

        // 新会话
        $('#newSessionBtn').on('click', function() {
            startNewSession();
        });

        // 回车提交（Ctrl+Enter）
        $('#questionInput').on('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                $('#uploadForm').submit();
            }
        });

        // 会话切换时重新加载文件列表
        $('#chatHistory').on('click', '.session-item', function() {
            setTimeout(loadFilesList, 500);
        });
    }

    // 处理文件选择
    function handleFileSelect(file) {
        if (!file) return;

        // 检查文件类型
        const allowedTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/json'];
        const allowedExtensions = ['.csv', '.xls', '.xlsx', '.parquet', '.json'];

        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

        if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
            showError('不支持的文件类型。请选择 CSV, Excel, Parquet 或 JSON 文件。');
            return;
        }

        // 检查文件大小（16MB限制）
        if (file.size > 16 * 1024 * 1024) {
            showError('文件大小不能超过 16MB。');
            return;
        }

        selectedFile = file;

        // 更新UI
        $('#dropText').addClass('hidden');
        $('#fileInfo').removeClass('hidden');
        $('#fileName').text(file.name);
        $('#dragArea').addClass('tech-glow');

        // 上传文件但不提问
        uploadFileOnly();
    }

    // 上传文件但不提问
    function uploadFileOnly() {
        if (!selectedFile) return;

        // 显示上传状态
        $('#uploadingStatus').removeClass('hidden');
        $('#fileInfo').addClass('hidden');
        $('#dropText').addClass('hidden');

        // 准备表单数据
        const formData = new FormData();
        formData.append('file', selectedFile);

        // 发送请求
        $.ajax({
            url: '/api/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            timeout: 60000,
            success: function(response) {
                $('#uploadingStatus').addClass('hidden');
                if (response.success) {
                    loadFilesList(); // 重新加载文件列表
                    // 显示文件信息
                    $('#fileInfo').removeClass('hidden');
                    addMessage('user', '已上传文件：' + selectedFile.name, selectedFile.name);
                    removeFile(); // 重置上传区域
                } else {
                    showError(response.error || '文件上传失败');
                    $('#fileInfo').removeClass('hidden');
                    $('#dropText').removeClass('hidden');
                }
            },
            error: function(xhr) {
                $('#uploadingStatus').addClass('hidden');
                $('#fileInfo').removeClass('hidden');
                $('#dropText').removeClass('hidden');
                let errorMsg = '';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 413) {
                    errorMsg = '文件太大，请选择较小的文件';
                } else if (xhr.status === 0) {
                    errorMsg = '网络连接失败';
                }
                if (errorMsg) {
                    showError(errorMsg);
                }
            }
        });
    }

    // 加载已上传文件列表
    function loadFilesList() {
        $.get('/api/files')
            .done(function(response) {
                const files = response.files || [];
                const selectElement = $('#selectedFile');
                
                // 清空选项，保留默认选项
                selectElement.find('option:not(:first)').remove();
                
                // 添加文件选项
                files.forEach(file => {
                    selectElement.append(`<option value="${file.id}">${file.filename}</option>`);
                });
            })
            .fail(function() {
                console.error('加载文件列表失败');
            });
    }

    // 移除文件
    function removeFile() {
        selectedFile = null;
        $('#fileInput').val('');
        $('#dropText').removeClass('hidden');
        $('#fileInfo').addClass('hidden');
        $('#dragArea').removeClass('tech-glow');
    }

    // 提交分析
    function submitAnalysis() {
        const selectedFileId = $('#selectedFile').val();
        const question = $('#questionInput').val().trim();
        
        if (!selectedFileId) {
            showError('请先选择一个已上传的文件。');
            return;
        }

        if (!question) {
            showError('请输入您的问题。');
            return;
        }

        // 显示加载状态
        showLoading(true);

        // 获取选中的文件名
        const filename = $('#selectedFile option:selected').text();
        
        // 添加用户消息到聊天区域
        addMessage('user', question, filename);

        // 发送请求
        $.ajax({
            url: '/api/ask_question',
            type: 'POST',
            contentType: 'application/json',
            dataType: 'json',  // 明确指定数据类型为JSON
            data: JSON.stringify({
                file_id: selectedFileId,
                question: question
            }),
            timeout: 60000,
            success: function(response) {
                showLoading(false);
                if (response.success) {
                    addMessage('ai', response.markdown_result, null, response.chat_id);
                    loadAllSessions(); // 重新加载会话列表
                    $('#questionInput').val(''); // 只清空问题输入框，保留文件选择
                } else {
                    showError(response.error || '分析失败');
                }
            },
            error: function(xhr, status, error) {
                showLoading(false);
                // 增加详细的错误日志输出，帮助调试
                console.log('AJAX Error:', status, error);
                console.log('XHR Status:', xhr.status);
                console.log('XHR Response:', xhr.responseText);
                
                let errorMsg = '';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 0) {
                    errorMsg = '网络连接失败';
                } else if (xhr.status === 500) {
                    errorMsg = '服务器内部错误';
                } else if (status === 'timeout') {
                    errorMsg = '请求超时，请重试';
                } else if (status === 'parsererror') {
                    errorMsg = '数据解析错误';
                    console.log('Response Text:', xhr.responseText);
                } else {
                    errorMsg = `请求失败: ${status} (${xhr.status})`;
                }
                
                if (errorMsg) {
                    showError(errorMsg);
                }
            }
        });
    }

    // 添加消息到聊天区域
    function addMessage(type, content, filename = null, chatId = null) {
        const timestamp = new Date().toLocaleString('zh-CN');
        let messageHtml = '';

        if (type === 'user') {
            messageHtml = `
                <div class="flex justify-end mb-4">
                    <div class="max-w-3xl">
                        <div class="bg-blue-600 rounded-lg p-4">
                            <div class="flex items-center mb-2">
                                <i class="fas fa-file-alt mr-2 text-blue-200"></i>
                                <span class="text-sm text-blue-200">${filename}</span>
                            </div>
                            <div class="text-white">${escapeHtml(content)}</div>
                            <div class="text-xs text-blue-200 mt-2">${timestamp}</div>
                        </div>
                    </div>
                </div>
            `;
        } else if (type === 'ai') {
            // content现在是markdown格式的字符串
            const markdownContent = content;

            messageHtml = `
                <div class="flex mb-4">
                    <div class="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center mr-3 flex-shrink-0 mt-1">
                        <i class="fas fa-robot text-sm"></i>
                    </div>
                    <div class="flex-1 max-w-4xl">
                        <div class="bg-gray-800 border border-gray-700 rounded-lg p-4">
                            <div class="markdown-content">${marked.parse(markdownContent)}</div>
                            <div class="text-xs text-gray-400 mt-3">${timestamp}</div>
                        </div>
                    </div>
                </div>
            `;
        }

        $('#chatMessages').append(messageHtml);
        scrollToBottom();
    }


    // 加载所有会话
    function loadAllSessions() {
        $.get('/api/sessions')
            .done(function(response) {
                allSessions = response.sessions || [];
                renderSessionList();
            })
            .fail(function() {
                console.error('加载会话列表失败');
            });
    }

    // 加载聊天历史
    function loadChatHistory() {
        $.get('/api/chat_history')
            .done(function(response) {
                chatHistory = response.history || [];
                renderCurrentChatHistory();
            })
            .fail(function() {
                console.error('加载聊天历史失败');
            });
    }

    // 渲染会话列表
    function renderSessionList() {
        const historyContainer = $('#chatHistory');

        if (allSessions.length === 0) {
            historyContainer.html(`
                <div class="text-gray-500 text-center text-sm py-8">
                    <i class="fas fa-history text-2xl mb-2 block"></i>
                    暂无聊天记录
                </div>
            `);
            return;
        }

        let historyHtml = '';
        allSessions.forEach(sessionInfo => {
            const date = new Date(sessionInfo.updated_at).toLocaleString('zh-CN');
            const title = sessionInfo.latest_question ?
                (sessionInfo.latest_question.length > 25 ? sessionInfo.latest_question.substring(0, 25) + '...' : sessionInfo.latest_question) :
                '新会话';
            const filename = sessionInfo.latest_filename || '';

            historyHtml += `
                <div class="bg-gray-700 hover:bg-gray-600 rounded p-3 cursor-pointer transition-colors session-item" data-session-id="${sessionInfo.id}">
                    <div class="flex items-center justify-between mb-1">
                        <div class="flex items-center">
                            <i class="fas fa-comments mr-2 text-blue-400 text-xs"></i>
                            <span class="text-xs text-gray-400">${sessionInfo.chat_count} 条对话</span>
                        </div>
                        <span class="text-xs text-gray-500">${new Date(sessionInfo.updated_at).toLocaleDateString('zh-CN')}</span>
                    </div>
                    <div class="text-sm text-gray-200 mb-1">${escapeHtml(title)}</div>
                    ${filename ? `<div class="text-xs text-gray-400"><i class="fas fa-file mr-1"></i>${filename}</div>` : ''}
                </div>
            `;
        });

        historyContainer.html(historyHtml);

        // 点击会话切换
        $('.session-item').on('click', function() {
            const sessionId = $(this).data('session-id');
            switchToSession(sessionId);
        });
    }

    // 渲染当前会话的聊天历史
    function renderCurrentChatHistory() {
        if (chatHistory.length === 0) {
            // 显示欢迎消息
            $('#chatMessages').html(`
                <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                    <div class="flex items-center mb-2">
                        <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-robot text-sm"></i>
                        </div>
                        <span class="font-semibold text-blue-400">AI助手</span>
                    </div>
                    <div class="text-gray-300">
                        欢迎使用AI数据分析助手！上传您的数据文件（支持CSV、Excel、Parquet、JSON格式），然后提出问题，我将为您生成SQL查询并分析数据。
                    </div>
                </div>
            `);
            return;
        }

        // 清空聊天区域并重新渲染所有消息
        $('#chatMessages').empty();
        chatHistory.forEach(chat => {
            addMessage('user', chat.question, chat.filename);
            const content = chat.markdown_result || chat.result;
            addMessage('ai', content, null, chat.id);
        });
    }

    // 切换到指定会话
    function switchToSession(sessionId) {
        $.post(`/api/switch_session/${sessionId}`)
            .done(function(response) {
                if (response.success) {
                    currentSessionId = sessionId;
                    loadChatHistory();
                    loadFilesList(); // 加载当前会话的文件列表

                    // 高亮当前选中的会话
                    $('.session-item').removeClass('bg-blue-700');
                    $(`.session-item[data-session-id="${sessionId}"]`).addClass('bg-blue-700');
                }
            })
            .fail(function() {
                showError('切换会话失败');
            });
    }

    // 开始新会话
    function startNewSession() {
        $.post('/api/new_session')
            .done(function(response) {
                if (response.session_id) {
                    currentSessionId = response.session_id;

                    // 清空当前聊天区域
                    chatHistory = [];
                    renderCurrentChatHistory();

                    // 重置表单
                    resetForm();

                    // 重新加载会话列表和文件列表以显示新会话
                    loadAllSessions();
                    loadFilesList();

                    // 清除会话高亮
                    $('.session-item').removeClass('bg-blue-700');
                }
            })
            .fail(function() {
                showError('创建新会话失败');
            });
    }

    // 重置表单
    function resetForm() {
        $('#questionInput').val('');
        $('#selectedFile').val(''); // 重置文件选择
        removeFile();
    }

    // 显示加载状态
    function showLoading(show) {
        if (show) {
            $('#loadingOverlay').removeClass('hidden');
            $('#submitBtn').prop('disabled', true);
            $('#submitText').text('分析中...');
        } else {
            $('#loadingOverlay').addClass('hidden');
            $('#submitBtn').prop('disabled', false);
            $('#submitText').text('分析');
        }
    }

    // 显示错误信息
    function showError(message) {
        const errorHtml = `
            <div class="flex mb-4">
                <div class="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
                    <i class="fas fa-exclamation-triangle text-sm"></i>
                </div>
                <div class="flex-1">
                    <div class="bg-red-900 border border-red-700 rounded-lg p-4">
                        <div class="text-red-300">${escapeHtml(message)}</div>
                    </div>
                </div>
            </div>
        `;
        $('#chatMessages').append(errorHtml);
        scrollToBottom();
    }

    // 滚动到底部
    function scrollToBottom() {
        const chatContainer = $('#chatMessages').parent();
        chatContainer.scrollTop(chatContainer[0].scrollHeight);
    }

    // HTML转义
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});