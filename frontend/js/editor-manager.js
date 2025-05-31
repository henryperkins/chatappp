// js/editor-manager.js - Monaco editor management
export class EditorManager {
    constructor() {
        this.editor = null;
        this.currentLanguage = 'javascript';
    }

    async init() {
        return new Promise((resolve) => {
            require.config({ paths: { vs: 'https://unpkg.com/monaco-editor@0.45.0/min/vs' } });
            require(['vs/editor/editor.main'], () => {
                this.createEditor();
                this.setupLanguageSelector();
                resolve();
            });
        });
    }

    createEditor() {
        this.editor = monaco.editor.create(document.getElementById('editor'), {
            value: '// Welcome to the code editor\n// Select text and use commands like /explain or /refactor',
            language: this.currentLanguage,
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: false },
            fontSize: 14,
            wordWrap: 'on'
        });

        // Add to message input on selection
        this.editor.onDidChangeCursorSelection((e) => {
            const selection = this.editor.getModel().getValueInRange(e.selection);
            if (selection) {
                window.selectedCode = selection;
            }
        });
    }

    setupLanguageSelector() {
        const selector = document.getElementById('languageSelect');
        selector.addEventListener('change', (e) => {
            this.currentLanguage = e.target.value;
            monaco.editor.setModelLanguage(this.editor.getModel(), this.currentLanguage);
        });
    }

    getSelectedText() {
        const selection = this.editor.getSelection();
        return this.editor.getModel().getValueInRange(selection);
    }

    getValue() {
        return this.editor.getValue();
    }

    setValue(value) {
        this.editor.setValue(value);
    }
}
