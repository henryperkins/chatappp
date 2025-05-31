// js/chat-ui.js - Chat UI management
export class ChatUI {
    constructor() {
        this.container = document.getElementById('messagesContainer');
        this.lastMessageElement = null;
        this.lastMessageRole = null;
    }

    renderMessages(messages) {
        this.container.innerHTML = '';
        messages.forEach(msg => this.addMessage(msg));
    }

    addMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.role} flex gap-3 p-4 rounded-lg ${message.role === 'user' ? 'bg-gray-800' : 'bg-gray-700'
            }`;

        const icon = document.createElement('div');
        icon.className = 'flex-shrink-0';
        icon.innerHTML = message.role === 'user'
            ? '<i class="fas fa-user-circle text-2xl"></i>'
            : '<i class="fas fa-robot text-2xl"></i>';

        const content = document.createElement('div');
        content.className = 'message-content flex-1';
        content.innerHTML = this.formatContent(message.content);

        messageEl.appendChild(icon);
        messageEl.appendChild(content);
        this.container.appendChild(messageEl);

        this.lastMessageElement = content;
        this.lastMessageRole = message.role;

        this.scrollToBottom();
    }

    appendToLastMessage(content) {
        if (!this.lastMessageElement || this.lastMessageRole !== 'assistant') {
            this.addMessage({ role: 'assistant', content: '' });
        }

        const currentContent = this.lastMessageElement.dataset.rawContent || '';
        const newContent = currentContent + content;
        this.lastMessageElement.dataset.rawContent = newContent;
        this.lastMessageElement.innerHTML = this.formatContent(newContent);
        this.scrollToBottom();
    }

    finalizeLastMessage() {
        if (this.lastMessageElement) {
            this.highlightCode();
        }
    }

    formatContent(content) {
        // Convert markdown to HTML
        return marked.parse(content, {
            highlight: (code, lang) => {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return hljs.highlightAuto(code).value;
            },
            breaks: true
        });
    }

    highlightCode() {
        this.container.querySelectorAll('pre code').forEach(block => {
            if (!block.classList.contains('hljs')) {
                hljs.highlightElement(block);
            }
        });
    }

    showError(message) {
        const errorEl = document.createElement('div');
        errorEl.className = 'message error bg-red-900 p-4 rounded-lg';
        errorEl.innerHTML = `<i class="fas fa-exclamation-triangle mr-2"></i>${message}`;
        this.container.appendChild(errorEl);
        this.scrollToBottom();
    }

    clear() {
        this.container.innerHTML = '';
        this.lastMessageElement = null;
        this.lastMessageRole = null;
    }

    scrollToBottom() {
        this.container.scrollTop = this.container.scrollHeight;
    }
}
