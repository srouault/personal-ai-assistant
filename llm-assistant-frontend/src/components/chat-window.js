import { LitElement, html, css } from 'lit';
import { styles } from '../styles.js';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.css';  // or another theme

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value;
      } catch (__) {}
    }
    return ''; // use external default escaping
  }
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

      .chat-container {
        display: flex;
        flex-direction: column;
        height: 100%;
        width: 100%;
        min-height: 0;
        overflow: hidden;
      }

      .messages-container {
        flex: 1 1 auto;
        min-height: 0;
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
      }

      .message-bubble pre {
        max-width: 100%;
        background-color: rgba(0, 0, 0, 0.1);
        border-radius: 4px;
        margin: 8px 0;
        position: relative;
      }

      .message-bubble code {
        font-family: monospace;
        font-size: 0.9em;
        padding: 0.2em 0.4em;
      }

      .message-bubble pre code {
        display: block;
        padding: 1em;
        overflow-x: auto;
        white-space: pre;
        line-height: 1.5;
        width: 100%;
      }

      .message-bubble pre code::-webkit-scrollbar {
        height: 8px;
      }

      .message-bubble pre code::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.1);
        border-radius: 4px;
      }

      .message-bubble pre code::-webkit-scrollbar-thumb {
        background: rgba(0, 0, 0, 0.3);
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
      }

      .title-container {
        flex: 0 0 auto;
        width: 100%;
      }

      .text-center {
        text-align: center;
      }

      .dot:nth-child(1) { animation-delay: 0s; }
      .dot:nth-child(2) { animation-delay: 0.3s; }
      .dot:nth-child(3) { animation-delay: 0.6s; }
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

  formatContent(message) {
    if (message.role === 'assistant') {
      return unsafeHTML(md.render(message.content));
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
  }

  render() {
    return html`
      <div class="chat-container">
        <div class="title-container border-b border-gray-200 bg-white py-6">
          <h1 class="text-2xl font-semibold text-gray-800 text-center m-0">Personal AI Assistant</h1>
        </div>

        <div class="messages-container bg-gray-100">
          <div class="messages-scroll space-y-4">
            ${this.messages.map((message, index) => html`
              <div class="flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}"
                   @rendered=${() => this.scrollToBottom()}>
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
              </div>
            `)}
          </div>
        </div>

        <div class="input-container border-t border-gray-200 bg-white p-4">
          <div class="flex space-x-4">
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