import { LitElement, html, css } from 'lit';
import { styles } from './styles.js';
import { marked } from 'marked';
import './components/chat-window.js';
import './components/context-panel.js';
import './components/chat-history.js';
import './components/learning-panel.js';

class LlmAssistantFrontend extends LitElement {
  static properties = {
    messages: { type: Array },
    inputText: { type: String },
    isLoading: { type: Boolean },
    waitingForFirstToken: { type: Boolean },
    selectedChatId: { type: Number },
    currentTutorial: { type: Object }
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
    this.currentTutorial = null;
    console.log('LlmAssistantFrontend initialized');
    this.initializeChat();
    this.addEventListener('start-tutorial', this.handleTutorialStart);
  }

  async initializeChat() {
    try {
      const response = await fetch('http://localhost:8080/chat/latest/id');
      if (response.ok) {
        const data = await response.json();
        this.selectedChatId = (data.id || 0) + 1;
        console.log('Initialized new chat with ID:', this.selectedChatId);
      } else {
        console.error('Failed to get latest chat ID');
      }
    } catch (error) {
      console.error('Error initializing chat:', error);
    }
  }

  async handleChatSelected(e) {
    const chatId = e.detail;
    this.selectedChatId = chatId;
    try {
      const response = await fetch(`http://localhost:8080/chats/${chatId}`);
      if (response.ok) {
        const chat = await response.json();
        console.log('Chat data:', chat);
        this.messages = chat.interactions.flatMap(interaction => [
          {
            ...interaction.messages.find(m => m.role === 'user'),
            interaction_id: interaction.interaction_id,
            timestamp: interaction.created_at
          },
          {
            ...interaction.messages.find(m => m.role === 'assistant'),
            interaction_id: interaction.interaction_id,
            timestamp: interaction.created_at
          }
        ].filter(Boolean));
        console.log('Processed messages:', this.messages);
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
    if (!this.inputText.trim()) return;

    if (!this.selectedChatId) {
      await this.initializeChat();
    }

    if (!this.selectedChatId) {
      console.error('Failed to initialize chat ID');
      return;
    }

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

  async handleNavigateToChat(e) {
    console.log('Navigation event received:', e.detail);
    const { chatId, interactionId } = e.detail;
    this.selectedChatId = chatId;
    
    try {
      console.log('Fetching chat:', chatId);
      const response = await fetch(`http://localhost:8080/chats/${chatId}`);
      if (response.ok) {
        const chat = await response.json();
        console.log('Received chat data:', chat);
        
        this.messages = chat.interactions.flatMap(interaction => [
          {
            ...interaction.messages.find(m => m.role === 'user'),
            interaction_id: interaction.interaction_id,
            timestamp: interaction.created_at
          },
          {
            ...interaction.messages.find(m => m.role === 'assistant'),
            interaction_id: interaction.interaction_id,
            timestamp: interaction.created_at
          }
        ].filter(Boolean));
        console.log('Updated messages:', this.messages);

        // Wait for messages to render then scroll to the interaction
        await this.updateComplete;
        
        // Add a small delay to ensure everything is rendered
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const chatWindow = this.shadowRoot.querySelector('chat-window');
        console.log('Found chat window:', chatWindow);
        
        if (chatWindow) {
          const scrollContainer = chatWindow.shadowRoot.querySelector('.messages-scroll');
          console.log('Found scroll container:', scrollContainer);
          
          if (scrollContainer) {
            const messageElement = scrollContainer.querySelector(
              `[data-interaction-id="${interactionId}"]`
            );
            console.log('Found message element:', messageElement);
            
            if (messageElement) {
              // Simple scroll calculation with smaller offset to show more context
              const scrollOffset = 150; // Increased from 100 to show more above the message
              const targetPosition = Math.max(0, messageElement.offsetTop - scrollOffset);
              
              // Get container height to ensure we don't scroll past bottom
              const containerHeight = scrollContainer.clientHeight;
              const maxScroll = scrollContainer.scrollHeight - containerHeight;
              const finalPosition = Math.min(targetPosition, maxScroll);
              
              scrollContainer.scrollTo({
                top: finalPosition,
                behavior: 'smooth'
              });
              console.log('Scrolled to position:', {
                targetPosition,
                finalPosition,
                offset: scrollOffset,
                containerHeight
              });
              
              // Add enhanced highlight effect
              messageElement.style.transition = 'background-color 0.5s ease-in-out';
              messageElement.style.backgroundColor = '#fef3c7'; // Warm yellow
              
              // Add a subtle border and shadow during highlight
              messageElement.style.boxShadow = '0 0 15px rgba(251, 191, 36, 0.4)';
              messageElement.style.borderRadius = '8px';
              
              setTimeout(() => {
                messageElement.style.backgroundColor = '';
                // Fade out the effects
                messageElement.style.boxShadow = '0 0 0 rgba(251, 191, 36, 0)';
                
                // Remove the transition after animation completes
                setTimeout(() => {
                  messageElement.style.transition = '';
                  messageElement.style.boxShadow = '';
                  messageElement.style.borderRadius = '';
                  console.log('Removed highlight effect');
                }, 500);
              }, 2000);
            } else {
              console.log('Message element not found for interaction:', interactionId);
            }
          } else {
            console.log('Scroll container not found');
          }
        } else {
          console.log('Chat window not found');
        }
      } else {
        console.error('Failed to fetch chat:', response.status);
      }
    } catch (error) {
      console.error('Error in handleNavigateToChat:', error);
    }
  }

  handleLearningQuestion(e) {
    const question = e.detail.question;
    this.inputText = question;
    this.sendMessage();
  }

  handleTutorialStart(event) {
    this.currentTutorial = event.detail;
    // Create an initial message to start the tutorial
    const initialMessage = `I'd like to start the tutorial "${event.detail.title}". Please guide me through it.`;
    
    // Add the message to the chat
    if (this.chatPanel) {
      this.chatPanel.addMessage({
        role: 'user',
        content: initialMessage
      });
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
            @navigate-to-chat=${this.handleNavigateToChat}
          ></chat-window>
          
          <context-panel></context-panel>
          <learning-panel @ask-question=${this.handleLearningQuestion}></learning-panel>
        </div>
      </div>
    `;
  }
}

customElements.define('llm-assistant-frontend', LlmAssistantFrontend);