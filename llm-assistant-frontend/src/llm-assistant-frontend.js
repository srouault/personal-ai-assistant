import { LitElement, html, css } from 'lit';
import { styles } from './styles.js';
import { marked } from 'marked';
import './components/chat-window.js';
import './components/context-panel.js';
import './components/chat-history.js';

class LlmAssistantFrontend extends LitElement {
  static properties = {
    messages: { type: Array },
    inputText: { type: String },
    isLoading: { type: Boolean },
    waitingForFirstToken: { type: Boolean },
    selectedChatId: { type: Number }
  };

  static styles = [
    styles,
    css`
      .app-container {
        display: flex;
        height: 100vh;
      }

      .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        max-width: calc(80vw - 300px);
      }
    `
  ];

  constructor() {
    super();
    this.messages = [];
    this.inputText = '';
    this.isLoading = false;
    this.waitingForFirstToken = false;
    this.selectedChatId = null;
  }

  async handleChatSelected(e) {
    const chatId = e.detail;
    this.selectedChatId = chatId;
    try {
      const response = await fetch(`http://localhost:8080/chats/${chatId}`);
      if (response.ok) {
        const chat = await response.json();
        // Flatten the interactions into messages
        this.messages = chat.interactions.flatMap(interaction => interaction.messages);
      }
    } catch (error) {
      console.error('Error loading chat:', error);
    }
  }

  async handleNewChat() {
    try {
      const response = await fetch('http://localhost:8000/chat/latest/id');
      const data = await response.json();
      const newChatId = (data.id || 0) + 1;
      this.selectedChatId = newChatId;
      this.messages = [];
      // Refresh chat list
      const chatHistoryElement = this.shadowRoot.querySelector('chat-history');
      if (chatHistoryElement) {
        chatHistoryElement.loadChats();
      }
    } catch (error) {
      console.error('Error creating new chat:', error);
    }
  }

  handleInputChange(e) {
    this.inputText = e.detail;
  }

  async sendMessage(e) {
    if (!this.inputText.trim() || !this.selectedChatId) return;

    const userMessage = {
      role: 'user',
      content: this.inputText.trim()
    };

    const contextPanel = this.shadowRoot.querySelector('context-panel');
    if (contextPanel) {
      contextPanel.fetchContext(this.inputText.trim())
        .catch(error => console.error('Error fetching context:', error));
    }

    this.messages = [...this.messages, userMessage];
    this.inputText = '';
    this.isLoading = true;
    this.waitingForFirstToken = true;

    const assistantMessage = {
      role: 'assistant',
      content: ''
    };
    this.messages = [...this.messages, assistantMessage];

    try {
      const response = await fetch(`http://localhost:8080/chat/stream?chat_id=${this.selectedChatId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          messages: this.messages.slice(0, -1),
          temperature: 0.7,
          max_tokens: 2000
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(5));
              if (data.text) {
                this.waitingForFirstToken = false;
                assistantMessage.content += data.text;
                this.messages = [...this.messages.slice(0, -1), assistantMessage];
              }
              if (data.error) {
                console.error('Error:', data.error);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      this.isLoading = false;
      this.waitingForFirstToken = false;
      // Refresh chat list to get updated summaries
      const chatHistoryElement = this.shadowRoot.querySelector('chat-history');
      if (chatHistoryElement) {
        chatHistoryElement.loadChats();
      }
    }
  }

  render() {
    return html`
      <div class="app-container">

        <div class="history_content">
          <chat-history
            .selectedChatId=${this.selectedChatId}
            @chat-selected=${this.handleChatSelected}
          ></chat-history>
        </div>
        
        <div class="main-content">
          <chat-window
            .messages=${this.messages}
            .inputText=${this.inputText}
            .isLoading=${this.isLoading}
            .waitingForFirstToken=${this.waitingForFirstToken}
            @input-change=${this.handleInputChange}
            @send-message=${this.sendMessage}
            @new-chat=${this.handleNewChat}
          ></chat-window>
          
          <context-panel></context-panel>
        </div>
      </div>
    `;
  }
}

customElements.define('llm-assistant-frontend', LlmAssistantFrontend);