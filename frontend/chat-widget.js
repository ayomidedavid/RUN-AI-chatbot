document.addEventListener('DOMContentLoaded', () => {
    // Inject the Chat Widget HTML
    const chatHtml = `
    <!-- Floating Chat Toggle Button -->
    <button class="chat-toggle-btn" id="chatToggleBtn" onclick="toggleChat()" title="Open Chat">
        <svg viewBox="0 0 24 24">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
        </svg>
    </button>

    <!-- Chat Widget -->
    <div class="chat-widget" id="chatWidget">
        <div class="chat-header" onclick="toggleChat()">
            <div class="avatar">RUN</div>
            <div class="header-info">
                <h2>Academic Chatbot</h2>
                <p><span class="status-dot"></span> Online</p>
            </div>
            <div class="close-btn">&times;</div>
        </div>

        <div class="chat-area" id="chatArea">
            <div class="message bot">
                Hello! I am your AI Academic Advisor. Whether you need information about electives, prerequisites, or graduation requirements, I'm here to help.
            </div>
            <div class="quick-actions">
                <button onclick="handleQuickAction('What can you do?')">What can you do?</button>
                <button onclick="handleQuickAction('How many units to graduate?')">Graduation Units</button>
                <button onclick="handleQuickAction('How is GPA calculated?')">GPA Formula</button>
            </div>
        </div>

        <div class="input-area">
            <input type="text" id="userInput" placeholder="Type your message..." autocomplete="off">
            <button id="sendBtn" title="Send">
                <svg viewBox="0 0 24 24">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path>
                </svg>
            </button>
        </div>
    </div>
    `;

    // document.body.insertAdjacentHTML('beforeend', chatHtml);

    // Bind logic
    const chatWidget = document.getElementById('chatWidget');
    const chatArea = document.getElementById('chatArea');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const API_BASE = window.location.protocol === 'file:'
        ? 'http://127.0.0.1:8001'
        : `http://${window.location.hostname}:8001`;

    window.toggleChat = function () {
        chatWidget.classList.toggle('active');
        if (chatWidget.classList.contains('active')) {
            userInput.focus();
        }
    }

    const parseMarkdown = (text) => {
        // Simple bold
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Lists
        if (text.includes('\n- ')) {
            const parts = text.split('\n- ');
            let html = parts[0] + '<ul>';
            for (let i = 1; i < parts.length; i++) {
                const item = parts[i].split('\n')[0];
                html += `<li>${item}</li>`;
            }
            html += '</ul>';
            // Handle remaining text after list if any
            const lastPart = parts[parts.length - 1];
            if (lastPart.includes('\n') && lastPart.split('\n').length > 1) {
                html += lastPart.split('\n').slice(1).join('<br>');
            }
            return html;
        }
        return text.replace(/\n/g, '<br>');
    };

    const appendMessage = (text, sender, thoughtProcessHtml = "") => {
        const div = document.createElement('div');
        div.className = `message ${sender}`;
        if (sender === 'bot') {
            div.innerHTML = thoughtProcessHtml + parseMarkdown(text);
        } else {
            div.innerText = text;
        }
        chatArea.appendChild(div);
        setTimeout(() => { chatArea.scrollTop = chatArea.scrollHeight; }, 50);
    };

    const appendTypingIndicator = () => {
        const div = document.createElement('div');
        div.className = 'typing-indicator';
        div.id = 'typingIndicator';
        div.innerHTML = '<div class="fidget-spinner"><div class="lobe"></div><div class="center"></div></div><span id="typingStatusText" style="margin-left:8px;">Loading...</span>';
        chatArea.appendChild(div);
        chatArea.scrollTop = chatArea.scrollHeight;
    };

    const removeTypingIndicator = () => {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    };

    const sendMessage = async () => {
        const text = userInput.value.trim();
        if (!text) return;

        appendMessage(text, 'user');
        userInput.value = '';

        appendTypingIndicator();

        try {
            const apiUrl = `${API_BASE}/api/chat`;
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: text })
            });

            if (!response.ok) throw new Error("API Error");

            const data = await response.json();
            
            const indicator = document.getElementById('typingIndicator');
            if (indicator) {
                indicator.innerHTML = `
                    <div class="fidget-spinner"><div class="lobe"></div><div class="center"></div></div>
                    <div style="display: flex; flex-direction: column; font-size: 0.8rem; margin-left: 8px;">
                        <span style="font-weight: bold; color: var(--primary);">Generating...</span>
                        <span style="color: var(--text-muted); margin-top: 2px;">Reasoning: ${data.intent.replace(/_/g, ' ')}</span>
                    </div>
                `;
                chatArea.scrollTop = chatArea.scrollHeight;
            }
            
            await new Promise(resolve => setTimeout(resolve, 300));
            
            removeTypingIndicator();

            let thoughtHtml = "";
            if (data.data && data.data.thought_process) {
                thoughtHtml = `
                <details class="thought-process">
                    <summary>View AI Thought Process</summary>
                    <div class="thought-process-content">
                        <strong>Intent Detected:</strong> ${data.intent}<br>
                        <strong>Factual Context Retrieved:</strong><br>
                        ${data.data.thought_process.replace(/\n/g, '<br>')}
                    </div>
                </details>
                `;
            }

            appendMessage(data.response, 'bot', thoughtHtml);

        } catch (error) {
            removeTypingIndicator();
            appendMessage("Sorry, I'm having trouble connecting to the advising server right now. Is the backend running?", 'bot');
            console.error(error);
        }
    };

    window.handleQuickAction = (text) => {
        userInput.value = text;
        sendMessage();
    };

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});
