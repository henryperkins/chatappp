// js/settings.js - Settings page logic
document.addEventListener('DOMContentLoaded', async () => {
    const form = document.getElementById('settingsForm');
    const temperatureSlider = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperatureValue');
    const maxTokensSlider = document.getElementById('maxTokens');
    const maxTokensValue = document.getElementById('maxTokensValue');
    const resetBtn = document.getElementById('resetBtn');
    const successMessage = document.getElementById('successMessage');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    // Update slider values
    temperatureSlider.addEventListener('input', (e) => {
        temperatureValue.textContent = e.target.value;
    });

    maxTokensSlider.addEventListener('input', (e) => {
        maxTokensValue.textContent = e.target.value;
    });

    // Load current settings
    async function loadSettings() {
        try {
            const response = await fetch('/api/settings', { credentials: 'include' });

            if (response.status === 401) {
                window.location.href = '/login.html';
                return;
            }
            if (!response.ok) throw new Error('Failed to load settings');

            const settings = await response.json();

            document.getElementById('model').value = settings.model;
            document.getElementById('temperature').value = settings.temperature;
            document.getElementById('maxTokens').value = settings.max_tokens;
            document.getElementById('provider').value = settings.provider;

            temperatureValue.textContent = settings.temperature;
            maxTokensValue.textContent = settings.max_tokens;

            // Also save to localStorage for frontend use
            localStorage.setItem('model', settings.model);
            localStorage.setItem('temperature', settings.temperature);
            localStorage.setItem('max_tokens', settings.max_tokens);
            localStorage.setItem('provider', settings.provider);
        } catch (error) {
            showError('Failed to load settings');
        }
    }

    // Save settings
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const settings = {
            model: formData.get('model'),
            temperature: parseFloat(formData.get('temperature')),
            max_tokens: parseInt(formData.get('maxTokens'))
        };

        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': sessionStorage.getItem('csrf_token')
                },
                credentials: 'include',
                body: JSON.stringify(settings)
            });

            if (response.status === 401) {
                window.location.href = '/login.html';
                return;
            }
            if (!response.ok) throw new Error('Failed to save settings');

            // Update localStorage
            Object.entries(settings).forEach(([key, value]) => {
                localStorage.setItem(key, value);
            });

            showSuccess();
        } catch (error) {
            showError('Failed to save settings');
        }
    });

    // Reset to defaults
    resetBtn.addEventListener('click', () => {
        document.getElementById('model').value = 'gpt-4o-mini';
        document.getElementById('temperature').value = '0.7';
        document.getElementById('maxTokens').value = '2048';
        document.getElementById('provider').value = 'openai';

        temperatureValue.textContent = '0.7';
        maxTokensValue.textContent = '2048';
    });

    function showSuccess() {
        successMessage.classList.remove('hidden');
        errorMessage.classList.add('hidden');
        setTimeout(() => {
            successMessage.classList.add('hidden');
        }, 3000);
    }

    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.remove('hidden');
        successMessage.classList.add('hidden');
    }

    // Initial load
    await loadSettings();
});
