$(document).ready(function() {
    let selectedFile = null;
    let chatHistory = [];

    // 初始化
    init();

    function init() {
        loadChatHistory();
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
        if (!selectedFile) {
            showError('请先选择一个文件。');
            return;
        }

        const question = $('#questionInput').val().trim();
        if (!question) {
            showError('请输入您的问题。');
            return;
        }

        // 显示加载状态
        showLoading(true);

        // 添加用户消息到聊天区域
        addMessage('user', question, selectedFile.name);

        // 准备表单数据
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('question', question);

        // 发送请求
        $.ajax({
            url: '/api/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            timeout: 60000,
            success: function(response) {
                showLoading(false);
                if (response.success) {
                    addMessage('ai', response.markdown_result, null, response.chat_id);
                    loadChatHistory();
                    resetForm();
                } else {
                    showError(response.error || '分析失败');
                }
            },
            error: function(xhr) {
                showLoading(false);
                let errorMsg = '服务器错误';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.status === 413) {
                    errorMsg = '文件太大，请选择较小的文件';
                } else if (xhr.status === 0) {
                    errorMsg = '网络连接失败';
                }
                showError(errorMsg);
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


    // 加载聊天历史
    function loadChatHistory() {
        $.get('/api/chat_history')
            .done(function(response) {
                chatHistory = response.history || [];
                renderChatHistory();
            })
            .fail(function() {
                console.error('加载聊天历史失败');
            });
    }

    // 渲染聊天历史
    function renderChatHistory() {
        const historyContainer = $('#chatHistory');

        if (chatHistory.length === 0) {
            historyContainer.html(`
                <div class="text-gray-500 text-center text-sm py-8">
                    <i class="fas fa-history text-2xl mb-2 block"></i>
                    暂无聊天记录
                </div>
            `);
            return;
        }

        let historyHtml = '';
        chatHistory.forEach(chat => {
            const date = new Date(chat.timestamp).toLocaleString('zh-CN');
            const preview = chat.question.length > 30 ? chat.question.substring(0, 30) + '...' : chat.question;

            historyHtml += `
                <div class="bg-gray-700 hover:bg-gray-600 rounded p-3 cursor-pointer transition-colors" data-chat-id="${chat.id}">
                    <div class="flex items-center mb-1">
                        <i class="fas fa-file-alt mr-2 text-blue-400 text-xs"></i>
                        <span class="text-xs text-gray-400">${chat.filename}</span>
                    </div>
                    <div class="text-sm text-gray-200 mb-1">${escapeHtml(preview)}</div>
                    <div class="text-xs text-gray-500">${date}</div>
                </div>
            `;
        });

        historyContainer.html(historyHtml);

        // 点击历史记录显示详情
        $('.bg-gray-700[data-chat-id]').on('click', function() {
            const chatId = $(this).data('chat-id');
            showChatDetail(chatId);
        });
    }

    // 显示聊天详情
    function showChatDetail(chatId) {
        const chat = chatHistory.find(c => c.id === chatId);
        if (!chat) return;

        // 清空当前聊天区域并显示选中的对话
        $('#chatMessages').empty();
        addMessage('user', chat.question, chat.filename);

        // 使用markdown_result如果存在，否则使用原始result
        const content = chat.markdown_result || chat.result;
        addMessage('ai', content, null, chat.id);
    }

    // 开始新会话
    function startNewSession() {
        $.post('/api/new_session')
            .done(function() {
                // 清空聊天区域
                $('#chatMessages').html(`
                    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                        <div class="flex items-center mb-2">
                            <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center mr-3">
                                <i class="fas fa-robot text-sm"></i>
                            </div>
                            <span class="font-semibold text-blue-400">AI助手</span>
                        </div>
                        <div class="text-gray-300">
                            欢迎使用AI数据分析助手！上传您的数据文件，然后提出问题，我将为您生成SQL查询并分析数据。
                        </div>
                    </div>
                `);
                resetForm();
                loadChatHistory();
            })
            .fail(function() {
                showError('创建新会话失败');
            });
    }

    // 重置表单
    function resetForm() {
        $('#questionInput').val('');
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