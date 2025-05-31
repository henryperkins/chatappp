// js/command-palette.js - Command palette implementation
export class CommandPalette {
    constructor() {
        this.element = document.getElementById('commandPalette');
        this.commands = [
            { command: '/explain', icon: 'fa-info-circle', description: 'Explain code' },
            { command: '/refactor', icon: 'fa-wrench', description: 'Refactor code' },
            { command: '/tests', icon: 'fa-vial', description: 'Generate tests' },
            { command: '/summarize', icon: 'fa-list', description: 'Summarize chat' }
        ];
        this.listeners = {};
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.element.querySelectorAll('.command-option').forEach(option => {
            option.addEventListener('click', () => {
                const command = option.dataset.command;
                this.emit('select', command);
                this.hide();
            });
        });
    }

    show(input) {
        const filtered = this.commands.filter(cmd =>
            cmd.command.startsWith(input.toLowerCase())
        );

        if (filtered.length > 0) {
            this.element.classList.remove('hidden');
        } else {
            this.hide();
        }
    }

    hide() {
        this.element.classList.add('hidden');
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
}
