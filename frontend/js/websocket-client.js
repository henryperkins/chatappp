// js/websocket-client.js - WebSocket client implementation
export class WebSocketClient {
    constructor() {
        this.ws = null;
        this.clientId = this.generateClientId();
        this.listeners = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    generateClientId() {
        return `client-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    connect() {
        // If already connected just return a resolved promise
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return Promise.resolve();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.clientId}`;

        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.emit('open');
                resolve();
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.emit('message', data);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
                reject(error);
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket disconnected');
                if (event.code !== 1008) {
                    this.attemptReconnect();
                }
            };
        });
    }

    async send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            throw new Error('WebSocket is not connected');
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
        }
    }

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }

    close() {
        if (this.ws) {
            this.ws.close();
        }
    }
}
