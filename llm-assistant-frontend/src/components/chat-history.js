import { LitElement, html, css } from 'lit';
import { styles } from '../styles.js';

export class ChatHistory extends LitElement {
  static properties = {
    chats: { type: Array },
    selectedChatId: { type: Number },
    loading: { type: Boolean }
  };

  static styles = [
    styles,
    css`
      :host {
        display: flex;
        flex-direction: column;
        margin-top: 0px;
        width: 300px;
        height: 100%;
        background-color: #1a1a1a;
      }

      .loading {
        opacity: 0.7;
        pointer-events: none;
      }

      .text-center {
        text-align: center;
        width: 100%;
        height: 70px;
        line-height: 32px;
        border-bottom: 1px solid #444;
        background-color: #1c1c1c;
      }

      .hist-panel {
        padding: 0.5rem;
      }

      .chat-item {
        padding: 12px;
        margin-bottom: 8px;
        border-radius: 8px;
        background-color: #2a2a2a;
        border: 1px solid #333;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .chat-item:hover {
        background-color: #333;
        transform: translateX(4px);
      }

      .chat-item.selected {
        background-color: #3a3a3a;
        border-color: #4a4a4a;
        position: relative;
      }

      .chat-item.selected::before {
        content: '';
        position: absolute;
        left: -0.5rem;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 70%;
        background-color: #3b82f6;
        border-radius: 2px;
      }

      .chat-date {
        font-size: 0.75rem;
        color: #888;
        margin-bottom: 4px;
      }

      .chat-summary {
        font-size: 0.875rem;
        color: #ccc;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        word-break: break-word;
      }

      .no-chats {
        color: #666;
        text-align: center;
        padding: 2rem;
        font-style: italic;
      }
    `
  ];

  constructor() {
    super();
    this.chats = [];
    this.selectedChatId = null;
    this.loading = false;
    this.loadChats();
  }

  async loadChats() {
    this.loading = true;
    try {
      const response = await fetch('http://localhost:8080/chats');
      if (response.ok) {
        this.chats = await response.json();
      } else {
        console.error('Failed to load chats');
      }
    } catch (error) {
      console.error('Error loading chats:', error);
    } finally {
      this.loading = false;
    }
  }

  formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      return date.toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit'
      });
    } else if (days === 1) {
      return 'Yesterday';
    } else if (days < 7) {
      return date.toLocaleDateString(undefined, { weekday: 'long' });
    } else {
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric'
      });
    }
  }

  handleChatClick(chatId) {
    this.selectedChatId = chatId;
    this.dispatchEvent(new CustomEvent('chat-selected', {
      detail: chatId
    }));
  }

  render() {
    return html`
      <div class="text-center">
        <h2>Chat History</h2>
      </div>

      <div class="hist-panel ${this.loading ? 'loading' : ''}">
        ${this.chats.length === 0 
          ? html`<div class="no-chats">No chat history found</div>`
          : this.chats.map(chat => html`
            <div 
              class="chat-item ${chat.id === this.selectedChatId ? 'selected' : ''}"
              @click=${() => this.handleChatClick(chat.id)}
            >
              <div class="chat-date">
                ${this.formatDate(chat.updated_at)}
              </div>
              <div class="chat-summary">
                ${chat.summary || 'No summary available'}
              </div>
            </div>
          `)}
      </div>
    `;
  }
}

customElements.define('chat-history', ChatHistory); 