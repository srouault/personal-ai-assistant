import { LitElement, html, css } from 'lit';
import { styles } from '../styles.js';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';
import MarkdownIt from 'markdown-it';
import './code-block.js';

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
  xhtmlOut: true
});

export class ChatWindow extends LitElement {
  static properties = {
    messages: { type: Array },
    inputText: { type: String },
    isLoading: { type: Boolean },
    waitingForFirstToken: { type: Boolean }
  };

  static styles = [
    styles,
    css`
      :host {
        display: flex;
        width: 100%;
        height: 100%;
        min-height: 0;
        margin: 0;
      }

      .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 2rem;
        border-bottom: 1px solid #555;
        background-color: #2a2a2a;

      }

      .title {
        font-size: 2rem;
        font-weight: 600;
        color: #e2e2e2;
        margin-left: auto;
        margin-right: auto;
      }

      .new-chat-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background-color: #2563eb;
        border: none;
        border-radius: 0.5rem;
        color: white;
        cursor: pointer;
        transition: background-color 0.2s;
      }

      .new-chat-btn:hover {
        background-color: #1d4ed8;
      }

      .new-chat-btn img {
        width: 20px;
        height: 20px;
      }

      .chat-container {
        display: flex;
        flex-direction: column;
        height: 100%;
        width: 100%;
        min-height: 0;
        max-height: calc(88vh);
        overflow: hidden;
      }

      .messages-container {
        flex: 1 1 auto;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }

      .messages-scroll {
        flex: 1;
        min-height: 0;
        padding: 1rem;
        overflow-y: auto;
        scroll-behavior: smooth;
      }

      .message-bubble {
        padding: 12px 16px;
        border-radius: 16px;
        word-break: break-word;
        max-width: 100%;
        box-sizing: border-box;
      }

      .message-bubble pre {
        margin: 8px -10px;
        background-color: #2d2d2d;
        border-radius: 4px;
        position: relative;
        box-sizing: border-box;
      }

      .message-bubble code {
        font-family: 'Fira Code', monospace;
        font-size: 0.9em;
        padding: 0.2em 0.4em;
      }

      .message-bubble pre code {
        display: block;
        padding: 1em;
        overflow-x: auto;
        white-space: pre;
        line-height: 1.5;
        margin: 0 10px;
        font-family: 'Fira Code', monospace;
      }

      .message-bubble pre[class*="language-"] {
        margin: 8px -10px;
        padding: 0;
        background: #2d2d2d;
      }

      .message-bubble code[class*="language-"] {
        padding: 1em;
        margin: 0 10px;
        background: none;
        text-shadow: none;
        font-family: 'Fira Code', monospace;
      }

      .message-bubble pre code::-webkit-scrollbar {
        height: 8px;
      }

      .message-bubble pre code::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.2);
        border-radius: 4px;
      }

      .message-bubble pre code::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
      }

      .user .message-bubble {
        border-bottom-right-radius: 4px;
      }

      .assistant .message-bubble {
        border-bottom-left-radius: 4px;
      }

      .input-container {
        flex: 0 0 auto;
        width: 100%;
        box-sizing: border-box;
      }

      .input-wrapper {
        display: flex;
        gap: 1rem;
        max-width: 100%;
        box-sizing: border-box;
        padding: 1rem;
      }

      textarea {
        flex: 1;
        min-width: 0;  /* Important for flex items */
        box-sizing: border-box;
      }

      button {
        flex-shrink: 0;  /* Prevent button from shrinking */
      }

      .title-container {
        flex: 0 0 auto;
        width: 100%;
        border-bottom: 1px solid #555;
      }

      .text-center {
        text-align: center;
      }

      .dot:nth-child(1) { animation-delay: 0s; }
      .dot:nth-child(2) { animation-delay: 0.3s; }
      .dot:nth-child(3) { animation-delay: 0.6s; }

      button[data-chat-id] {
        cursor: pointer;
        transition: background-color 0.2s;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 2.5rem;
        line-height: 1;
      }

      .take-me-there-btn {
        width: 120px;
        padding: 0px;
        padding-bottom: 10px;
        font-weight: bold;
      }

      button[data-chat-id]:hover {
        background-color: #3b82f6;
      }

      .message-bubble button {
        margin-top: 8px;
      }

      .message-timestamp {
        font-size: 0.75rem;
        color: #6b7280;
        margin: 2px 8px;
        opacity: 0.8;
      }

      .user .message-timestamp {
        text-align: right;
      }

      .assistant .message-timestamp {
        text-align: left;
      }

      .message-container {
        display: flex;
        flex-direction: column;
        margin: 5px;
        padding: 0;
      }

      .user .message-container {
        align-items: flex-end;
      }

      .assistant .message-container {
        align-items: flex-start;
      }

      .messages-scroll {
        flex: 1;
        min-height: 0;
        padding: 1rem;
        overflow-y: auto;
        scroll-behavior: smooth;
      }

      .messages-scroll > div.flex {
        margin: 0;
        padding: 0;
      }

      .messages-scroll > div.flex + div.flex {
        margin-top: 0.5rem;
      }
    `
  ];

  handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      this.dispatchEvent(new CustomEvent('send-message'));
    }
  }

  handleInput(e) {
    this.dispatchEvent(new CustomEvent('input-change', {
      detail: e.target.value
    }));
  }

  processMessageContent(content) {
    if (!content) return '';
    
    const regex = /<<<chat_history>>>(\d+),(\d+)<<<chat_history>>>/;
    const match = content.match(regex);
    
    if (match) {
      const [fullMatch, chatId, interactionId] = match;
      console.log('Found chat history link:', { chatId, interactionId });
      
      const buttonHtml = `<button 
        class="bg-blue-500 hover:bg-blue-700 text-white font-bold take-me-there-btn"
        data-chat-id="${chatId}" 
        data-interaction-id="${interactionId}">
        Take Me There
      </button>`;
      
      console.log('Generated button HTML:', buttonHtml);
      return content.replace(fullMatch, buttonHtml);
    }
    
    return content;
  }

  formatContent(message) {
    if (message.role === 'assistant') {
      // console.log('Formatting assistant message:', message);
      const content = this.processMessageContent(message.content);
      // console.log('Processed content:', content);
      const segments = [];
      let currentPosition = 0;

      while (currentPosition < content.length) {
        const nextCodeBlock = content.indexOf('```', currentPosition);

        if (nextCodeBlock === -1) {
          if (currentPosition < content.length) {
            segments.push({
              type: 'text',
              content: content.slice(currentPosition)
            });
          }
          break;
        }

        if (nextCodeBlock > currentPosition) {
          segments.push({
            type: 'text',
            content: content.slice(currentPosition, nextCodeBlock)
          });
        }

        const codeStart = content.indexOf('\n', nextCodeBlock + 3);
        const codeEnd = content.indexOf('```', codeStart);
        
        const language = content.slice(nextCodeBlock + 3, codeStart).trim();

        if (codeEnd === -1) {
          segments.push({
            type: 'code',
            language: language || 'text',
            content: content.slice(codeStart + 1)
          });
          break;
        } else {
          segments.push({
            type: 'code',
            language: language || 'text',
            content: content.slice(codeStart + 1, codeEnd)
          });
          currentPosition = codeEnd + 3;
        }
      }

      return html`
        ${segments.map(segment => {
          if (segment.type === 'code') {
            return html`<code-block .language=${segment.language} .code=${segment.content}></code-block>`;
          } else {
            return unsafeHTML(md.render(segment.content));
          }
        })}
      `;
    }
    return message.content;
  }

  scrollToBottom() {
    requestAnimationFrame(() => {
      const container = this.shadowRoot.querySelector('.messages-scroll');
      if (container) {
        const scrollHeight = container.scrollHeight;
        container.scrollTo({
          top: scrollHeight,
          behavior: 'smooth'
        });
      }
    });
  }

  updated(changedProperties) {
    if (changedProperties.has('messages')) {
      this.scrollToBottom();
    }
  }

  async firstUpdated() {
    this.scrollToBottom();
    
    // Debug button rendering
    setTimeout(() => {
      const buttons = this.shadowRoot.querySelectorAll('button[data-chat-id]');
      console.log('Found navigation buttons:', buttons.length);
      buttons.forEach(button => {
        console.log('Button data:', {
          chatId: button.dataset.chatId,
          interactionId: button.dataset.interactionId,
          html: button.outerHTML
        });
      });
    }, 1000);
  }

  constructor() {
    super();
    this.messages = [];
    this.inputText = '';
    this.isLoading = false;
    this.waitingForFirstToken = false;
  }

  connectedCallback() {
    super.connectedCallback();
    console.log('Adding click event listener');
    this.addEventListener('click', this._handleClick);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    console.log('Removing click event listener');
    this.removeEventListener('click', this._handleClick);
  }

  _handleClick = (e) => {
    console.log('Click event received in chat-window:', e.target);
    
    const button = e.target.closest('button[data-chat-id]');
    console.log('Found button:', button);
    
    if (button) {
      e.preventDefault();
      e.stopPropagation();
      
      const chatId = parseInt(button.dataset.chatId);
      const interactionId = parseInt(button.dataset.interactionId);
      
      console.log('Attempting navigation with:', { chatId, interactionId });
      
      try {
        const event = new CustomEvent('navigate-to-chat', {
          detail: { chatId, interactionId },
          bubbles: true,
          composed: true
        });
        console.log('Dispatching navigation event:', event);
        this.dispatchEvent(event);
        console.log('Navigation event dispatched');
      } catch (error) {
        console.error('Error dispatching navigation event:', error);
      }
    }
  };

  formatTimestamp(timestamp) {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      // Today - show time only
      return date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit'
      });
    } else if (diffInHours < 48) {
      // Yesterday
      return `Yesterday at ${date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit'
      })}`;
    } else {
      // Older - show date and time
      return date.toLocaleDateString([], { 
        month: 'short', 
        day: 'numeric' 
      }) + ' at ' + date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit'
      });
    }
  }

  render() {
    return html`
      <div class="chat-container">
        <div class="header-container">
          <div class="title">Personal AI Assistant</div>
          <button class="new-chat-btn" @click=${() => window.location.reload()}>
            <img src="/assets/compose_3.png" alt="New Chat">
            New Chat
          </button>
        </div>

        <div class="messages-container bg-gray-100">
          <div class="messages-scroll" @click=${this._handleClick}>
            ${this.messages.map((message, index) => html`
              <div class="flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}"
                   data-interaction-id="${message.interaction_id}">
                <div class="message-container">
                  <div class="${message.role === 'user' 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-white text-gray-800'} 
                    message-bubble shadow-sm markdown-body">
                    ${this.formatContent(message)}
                    ${message.role === 'assistant' && 
                      index === this.messages.length - 1 && 
                      this.waitingForFirstToken ? html`
                      <div class="typing-indicator">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                      </div>
                    ` : ''}
                  </div>
                  ${message.timestamp ? html`
                    <div class="message-timestamp">
                      ${this.formatTimestamp(message.timestamp)}
                    </div>
                  ` : ''}
                </div>
              </div>
            `)}
          </div>
        </div>

        <div class="input-container border-t border-gray-200 bg-white">
          <div class="input-wrapper">
            <textarea
              class="flex-1 border border-gray-200 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="1"
              placeholder="Type your message..."
              .value=${this.inputText}
              @input=${this.handleInput}
              @keypress=${this.handleKeyPress}
              ?disabled=${this.isLoading}
            ></textarea>
            <button
              class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-400"
              @click=${() => this.dispatchEvent(new CustomEvent('send-message'))}
              ?disabled=${this.isLoading}
            >
              ${this.isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('chat-window', ChatWindow);
