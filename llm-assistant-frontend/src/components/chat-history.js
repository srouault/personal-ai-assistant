import { LitElement, html, css } from 'lit';
import { styles } from '../styles.js';

export class ChatHistory extends LitElement {
  static properties = {
    chats: { type: Array },
    selectedChatId: { type: Number },
    loading: { type: Boolean },
    showDeleteModal: { type: Boolean },
    chatToDelete: { type: Number },
    expandedChats: { type: Object }
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
        flex-shrink: 0;
      }

      .hist-panel {
        padding: 0.5rem;
        flex: 1;
        overflow-y: auto;
        scrollbar-width: thin;
        scrollbar-color: #444 #1a1a1a;
      }

      .hist-panel::-webkit-scrollbar {
        width: 8px;
      }

      .hist-panel::-webkit-scrollbar-track {
        background: #1a1a1a;
      }

      .hist-panel::-webkit-scrollbar-thumb {
        background-color: #444;
        border-radius: 4px;
        border: 2px solid #1a1a1a;
      }

      .hist-panel::-webkit-scrollbar-thumb:hover {
        background-color: #555;
      }

      .chat-item {
        padding: 12px;
        margin-bottom: 8px;
        border-radius: 8px;
        background-color: #2a2a2a;
        border: 1px solid #333;
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
        display: flex;
        flex-direction: column;
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

      .chat-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
      }

      .chat-type {
        display: flex;
        align-items: center;
        font-size: 0.75rem;
        padding: 2px 6px;
        border-radius: 4px;
        background-color: #333;
        color: #888;
      }

      .chat-type.tutorial {
        background-color: #1a472a;
        color: #4ade80;
      }

      .chat-type svg {
        width: 12px;
        height: 12px;
        margin-right: 4px;
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

      .delete-btn {
        display: block;
        position: absolute;
        right: 8px;
        top: 8px;
        width: 48px;
        height: 48px;
        padding: 4px;
        border-radius: 4px;
        background: transparent;
        border: none;
        cursor: pointer;
        opacity: 0;
        transition: all 0.2s ease;
      }

      .chat-item:hover .delete-btn {
        opacity: 1;
      }

      .delete-btn:hover {
        background-color: #ff4444;
      }

      .delete-btn img {
        width: 100%;
        height: 100%;
        filter: invert(0.6);
      }

      .delete-btn:hover img {
        filter: invert(1);
      }

      .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
      }

      .modal {
        background-color: #2a2a2a;
        padding: 1.5rem;
        border-radius: 8px;
        min-width: 300px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      }

      .modal-title {
        font-size: 1.2rem;
        color: #e2e2e2;
        margin-bottom: 1rem;
      }

      .modal-buttons {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 1.5rem;
      }

      .modal-btn {
        padding: 0.5rem 1rem;
        border-radius: 4px;
        border: none;
        cursor: pointer;
        font-weight: 500;
      }

      .cancel-btn {
        background-color: #4a4a4a;
        color: #e2e2e2;
      }

      .confirm-btn {
        background-color: #ff4444;
        color: white;
      }

      .cancel-btn:hover {
        background-color: #5a5a5a;
      }

      .confirm-btn:hover {
        background-color: #ff5555;
      }

      .chat-progress {
        width: 100%;
        height: 8px;
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        overflow: hidden;
        margin-top: 4px;
        position: relative;
      }

      .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%);
        box-shadow: 0 0 10px rgba(74, 222, 128, 0.4);
        transition: width 0.3s ease;
        border-radius: 4px;
      }

      .progress-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 50%;
        background: linear-gradient(
          to bottom,
          rgba(255, 255, 255, 0.2),
          transparent
        );
      }

      .progress-text {
        font-size: 0.75rem;
        color: #4ade80;
        font-weight: 500;
        min-width: 60px;
        text-align: right;
      }

      .chat-type.tutorial {
        display: flex;
        flex-direction: column;
      }

      .tutorial-status {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 4px;
      }

      .tutorial-progress-section {
        display: flex;
        margin-top: 3px;
        flex-direction: column;
        padding: 6px 0;
        gap: 4px;
      }

      .progress-stats {
        display: flex;
        align-items: center;
        font-size: 0.75rem;
        color: #888;
      }

      .steps-count {
        color: #888;
      }

      .percentage {
        color: #4ade80;
        font-weight: 500;
      }

      .tutorial-details {
        margin-top: 8px;
        padding-left: 8px;
        border-left: 2px solid #3b82f6;
      }

      .expand-button {
        background: none;
        border: none;
        color: #4ade80;
        cursor: pointer;
        padding: 4px;
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 0.75rem;
        margin-top: 4px;
      }

      .expand-button:hover {
        color: #22c55e;
      }

      .expand-icon {
        transition: transform 0.2s ease;
      }

      .expand-icon.expanded {
        transform: rotate(90deg);
      }

      .chapter-item {
        margin: 8px 0;
        font-size: 0.875rem;
        color: #e2e2e2;
      }

      .chapter-title {
        font-weight: 500;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .step-list {
        padding-left: 16px;
        margin: 4px 0;
      }

      .step-item {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #888;
        font-size: 0.75rem;
        margin: 4px 0;
      }

      .step-item.completed {
        color: #4ade80;
      }

      .checkmark {
        width: 14px;
        height: 14px;
        color: #4ade80;
      }

      .chapter-progress {
        font-size: 0.75rem;
        color: #888;
        margin-left: auto;
      }
    `
  ];

  constructor() {
    super();
    this.chats = [];
    this.selectedChatId = null;
    this.loading = false;
    this.showDeleteModal = false;
    this.chatToDelete = null;
    this.expandedChats = {};
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
      return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } else if (days === 1) {
      return `Yesterday ${date.toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit'
      })}`;
    } else if (days < 7) {
      return date.toLocaleString(undefined, {
        weekday: 'long',
        hour: '2-digit',
        minute: '2-digit'
      });
    } else {
      return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  }

  handleChatClick(chatId) {
    this.selectedChatId = chatId;
    this.dispatchEvent(new CustomEvent('chat-selected', {
      detail: chatId
    }));
  }

  async deleteChat(chatId) {
    try {
      // Delete chat from backend
      const response = await fetch(`http://localhost:8080/chats/${chatId}`, {
        method: 'DELETE'
      });

      // Delete tutorial progress from docstore
      const progressResponse = await fetch(`http://localhost:8001/progress/${chatId}`, {
        method: 'DELETE'
      });

      if (!progressResponse.ok) {
        console.error('Failed to delete tutorial progress:', await progressResponse.text());
      }

      if (response.ok) {
        // Remove from local list
        this.chats = this.chats.filter(chat => chat.id !== chatId);
        
        // If deleted chat was selected, clear selection
        if (chatId === this.selectedChatId) {
          this.selectedChatId = null;
          this.dispatchEvent(new CustomEvent('chat-selected', { detail: null }));
        }
      } else {
        console.error('Failed to delete chat');
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  }

  handleDeleteClick(e, chatId) {
    e.stopPropagation();  // Prevent chat selection when clicking delete
    this.chatToDelete = chatId;
    this.showDeleteModal = true;
  }

  handleConfirmDelete() {
    if (this.chatToDelete) {
      this.deleteChat(this.chatToDelete);
    }
    this.showDeleteModal = false;
    this.chatToDelete = null;
  }

  handleCancelDelete() {
    this.showDeleteModal = false;
    this.chatToDelete = null;
  }

  toggleExpand(e, chatId) {
    e.stopPropagation();
    this.expandedChats = {
      ...this.expandedChats,
      [chatId]: !this.expandedChats[chatId]
    };
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
              <button 
                class="delete-btn"
                @click=${(e) => this.handleDeleteClick(e, chat.id)}
              >
                <img src="/assets/trash.png" alt="Delete">
              </button>
              <div class="chat-header">
                <div class="chat-type ${chat.tutorial ? 'tutorial' : ''}">
                  ${chat.tutorial ? html`
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 14l9-5-9-5-9 5 9 5z"/>
                      <path d="M12 16l-9-5v7l9 5 9-5v-7l-9 5z"/>
                    </svg>
                    Tutorial
                  ` : html`
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
                    </svg>
                    Chat
                  `}
                </div>
                <div class="chat-date">
                  ${this.formatDate(chat.updated_at)}
                </div>
              </div>

              <div class="chat-summary">
                ${chat.tutorial ? chat.tutorial.title : (chat.summary || 'No summary available')}
              </div>

              ${chat.tutorial?.progress ? html`
                <div class="tutorial-progress-section">
                  <div class="progress-stats">
                    ${chat.tutorial.progress.completed_steps}/${chat.tutorial.progress.total_steps} steps
                  </div>
                  <div class="chat-progress">
                    <div class="progress-bar" 
                         style="width: ${chat.tutorial.progress.progress_percentage}%">
                    </div>
                  </div>
                  <button class="expand-button" @click=${(e) => this.toggleExpand(e, chat.id)}>
                    <svg 
                      class="expand-icon ${this.expandedChats[chat.id] ? 'expanded' : ''}"
                      width="12" 
                      height="12" 
                      viewBox="0 0 24 24" 
                      fill="currentColor"
                    >
                      <path d="M8 5v14l11-7z"/>
                    </svg>
                    ${this.expandedChats[chat.id] ? 'Hide Details' : 'Show Details'}
                  </button>
                </div>

                ${this.expandedChats[chat.id] ? html`
                  <div class="tutorial-details">
                    ${chat.tutorial.chapters.map((chapter, chapterIndex) => {
                      const chapterSteps = chapter.steps || [];
                      
                      // Calculate total steps completed before this chapter
                      const previousChaptersSteps = chat.tutorial.chapters
                        .slice(0, chapterIndex)
                        .reduce((total, ch) => total + (ch.steps?.length || 0), 0);
                      
                      // Calculate completed steps for this chapter
                      const completedSteps = chapterSteps.filter(step => 
                        (step.order + previousChaptersSteps) <= chat.tutorial.progress.completed_steps
                      ).length;
                      
                      return html`
                        <div class="chapter-item">
                          <div class="chapter-title">
                            ${chapter.title}
                            <span class="chapter-progress">
                              ${completedSteps}/${chapterSteps.length}
                            </span>
                          </div>
                          <div class="step-list">
                            ${chapter.steps.map(step => {
                              const stepGlobalPosition = step.order + previousChaptersSteps;
                              const isCompleted = stepGlobalPosition <= chat.tutorial.progress.completed_steps;
                              return html`
                                <div class="step-item ${isCompleted ? 'completed' : ''}">
                                  ${isCompleted ? html`
                                    <svg class="checkmark" viewBox="0 0 24 24">
                                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                                    </svg>
                                  ` : html`
                                    <svg class="checkmark" viewBox="0 0 24 24" style="opacity: 0.3">
                                      <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
                                    </svg>
                                  `}
                                  ${step.title}
                                </div>
                              `;
                            })}
                          </div>
                        </div>
                      `;
                    })}
                  </div>
                ` : ''}
              ` : ''}
            </div>
          `)}
      </div>

      ${this.showDeleteModal ? html`
        <div class="modal-backdrop">
          <div class="modal">
            <div class="modal-title">Delete Chat</div>
            <div>Are you sure you want to delete this chat?</div>
            <div class="modal-buttons">
              <button class="modal-btn cancel-btn" @click=${this.handleCancelDelete}>
                Cancel
              </button>
              <button class="modal-btn confirm-btn" @click=${this.handleConfirmDelete}>
                Delete
              </button>
            </div>
          </div>
        </div>
      ` : ''}
    `;
  }
}

customElements.define('chat-history', ChatHistory); 