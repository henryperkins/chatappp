// js/search-manager.js - Search functionality
export class SearchManager {
    constructor() {
        this.messagesContainer = document.getElementById('messagesContainer');
    }

    search(query) {
        const messages = this.messagesContainer.querySelectorAll('.message');
        const lowerQuery = query.toLowerCase();

        messages.forEach(message => {
            const content = message.textContent.toLowerCase();
            if (query === '' || content.includes(lowerQuery)) {
                message.classList.remove('hidden');
                this.highlightText(message, query);
            } else {
                message.classList.add('hidden');
            }
        });
    }

    highlightText(element, query) {
        if (!query) {
            // Remove existing highlights
            element.querySelectorAll('.highlight').forEach(span => {
                const parent = span.parentNode;
                parent.replaceChild(document.createTextNode(span.textContent), span);
                parent.normalize();
            });
            return;
        }

        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        const textNodes = [];
        while (walker.nextNode()) {
            textNodes.push(walker.currentNode);
        }

        textNodes.forEach(node => {
            const text = node.textContent;
            const regex = new RegExp(`(${query})`, 'gi');
            if (regex.test(text)) {
                const span = document.createElement('span');
                span.innerHTML = text.replace(regex, '<span class="highlight bg-yellow-500 text-black">$1</span>');
                node.parentNode.replaceChild(span, node);
            }
        });
    }
}
