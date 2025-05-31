// js/app.js - Main frontend application logic
import { ChatUI } from './chat-ui.js';
import { EditorManager } from './editor-manager.js';
import { WebSocketClient } from './websocket-client.js';
import { CommandPalette } from './command-palette.js';
import { SearchManager } from './search-manager.js';

class App {
    constructor() {
        this.chatUI = new ChatUI();
        this.editorManager = new EditorManager();
        this.wsClient = new WebSocketClient();
        this.commandPalette = new CommandPalette();
        this.searchManager = new SearchManager();
        this.abortController = null;
        this.csrfToken = sessionStorage.getItem('csrf_token');
    }

    async init() {
        await this.editorManager.init();
        this.setupEventListeners();
        await this.loadChatHistory();
        await this.wsClient.connect();
    }

    setupEventListeners() {
        // Message input handling
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const abortBtn = document.getElementById('abortBtn');
        const clearChatBtn = document.getElementById('clearChatBtn');
        const logoutBtn = document.getElementById('logoutBtn');
        const searchInput = document.getElementById('searchInput');

        sendBtn.addEventListener('click', () => this.sendMessage());
        abortBtn.addEventListener('click', () => this.abortGeneration());
        clearChatBtn.addEventListener('click', () => this.clearChat());
        logoutBtn.addEventListener('click', () => this.logout());

        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Command palette
        messageInput.addEventListener('input', (e) => {
            const value = e.target.value;
            if (value.startsWith('/')) {
                this.commandPalette.show(value);
            } else {
                this.commandPalette.hide();
            }
        });

        // Command selection
        this.commandPalette.on('select', (command) => {
            messageInput.value = command + ' ';
            messageInput.focus();
        });

        // Search functionality
        searchInput.addEventListener('input', (e) => {
            this.searchManager.search(e.target.value);
        });

        // WebSocket message handling
        this.wsClient.on('message', (data) => this.handleWebSocketMessage(data));
        this.wsClient.on('error', (error) => this.handleWebSocketError(error));
    }

    async loadChatHistory() {
        try {
            const response = await fetch('/api/chat/history', {
                credentials: 'include'
            });

            if (!response.ok) throw new Error('Failed to load chat history');

            const data = await response.json();
            this.chatUI.renderMessages(data.messages);
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const content = messageInput.value.trim();

        if (!content) return;

        // Parse command if present
        let command = null;
        let actualContent = content;

        if (content.startsWith('/')) {
            const parts = content.split(' ');
            command = parts[0];
            actualContent = parts.slice(1).join(' ');
        }

        // Add user message to UI
        this.chatUI.addMessage({
            role: 'user',
            content: actualContent
        });

        // Clear input and show abort button
        messageInput.value = '';
        this.toggleAbortButton(true);

        // Send via WebSocket
        await this.wsClient.send({
            type: 'message',
            content: actualContent,
            command: command,
            temperature: parseFloat(localStorage.getItem('temperature') || '0.7'),
            max_tokens: parseInt(localStorage.getItem('max_tokens') || '2048')
        });
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'content':
                this.chatUI.appendToLastMessage(data.data);
                break;
            case 'done':
                this.toggleAbortButton(false);
                this.chatUI.finalizeLastMessage();
                break;
            case 'error':
                this.toggleAbortButton(false);
                this.chatUI.showError(data.error);
                break;
        }
    }

    handleWebSocketError(error) {
        console.error('WebSocket error:', error);
        this.chatUI.showError('Connection error. Please refresh the page.');
        this.toggleAbortButton(false);
    }

    async abortGeneration() {
        await this.wsClient.send({ type: 'abort' });
        this.toggleAbortButton(false);
    }

    async clearChat() {
        if (!confirm('Clear all chat history?')) return;

        try {
            const response = await fetch('/api/chat/history', {
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    'X-CSRF-Token': this.csrfToken
                }
            });

            if (!response.ok) throw new Error('Failed to clear chat');

            this.chatUI.clear();
        } catch (error) {
            console.error('Failed to clear chat:', error);
        }
    }

    async logout() {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-CSRF-Token': this.csrfToken
                }
            });
            window.location.href = '/login.html';
        } catch (error) {
            console.error('Logout failed:', error);
        }
    }

    toggleAbortButton(show) {
        document.getElementById('sendBtn').classList.toggle('hidden', show);
        document.getElementById('abortBtn').classList.toggle('hidden', !show);
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    const app = new App();
    await app.init();
});
