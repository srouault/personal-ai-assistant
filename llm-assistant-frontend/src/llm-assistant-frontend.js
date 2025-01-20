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
    currentTutorial: { type: Object },
    currentTutorialProgress: { type: Object },
    waitingForChapterConfirmation: { type: Boolean },
    lastConfirmationResponse: { type: Boolean },
    currentStepProgress: { type: Object },
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
    this.currentTutorialProgress = {
      tutorialId: null,
      currentChapter: 0,
      completedChapters: []
    };
    this.waitingForChapterConfirmation = false;
    this.lastConfirmationResponse = null;
    this.currentStepProgress = {
      currentStep: 0,
      completedSteps: [],
      lastConfirmation: null,
      totalSteps: 0
    };
    console.log('LlmAssistantFrontend initialized');
    this.initializeChat();
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

  async handleChatSelected(event) {
    const chatId = event.detail;
    this.selectedChatId = chatId;
    console.log('Selected chat:', chatId);

    try {
        // Load chat messages
        const response = await fetch(`http://localhost:8080/chats/${chatId}`);
        if (response.ok) {
            const chat = await response.json();
            console.log('Chat data:', chat);
            
            // Transform interactions into flat messages array
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
        }

        // Load tutorial progress for this chat
        const progressResponse = await fetch(`http://localhost:8001/tutorial_chat/${chatId}`);
        if (progressResponse.ok) {
            const progress = await progressResponse.json();
            if (progress.tutorial_id) {
                // Load tutorial details
                const tutorialResponse = await fetch(`http://localhost:8001/tutorials/${progress.tutorial_id}`);
                if (tutorialResponse.ok) {
                    const tutorial = await tutorialResponse.json();
                    this.currentTutorial = tutorial;
                    this.currentTutorialProgress = {
                        tutorialId: tutorial.id,
                        currentChapter: progress.current_chapter || 0,
                        completedChapters: progress.completed_chapters || []
                    };
                    
                    // Add step progress state
                    this.currentStepProgress = {
                        currentStep: progress.current_step || 0,
                        completedSteps: progress.completed_steps || [],
                        totalSteps: progress.total_steps || 0,
                        lastConfirmation: null
                    };
                    
                    console.log('Loaded tutorial state:', {
                        tutorial: this.currentTutorial,
                        progress: this.currentTutorialProgress,
                        stepProgress: this.currentStepProgress
                    });
                }
            }
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
    // If called programmatically without an event (e.g. from handleTutorialStart)
    if (!e && !this.inputText.trim()) return;
    
    // If called from a button click event
    if (e && e.detail && !e.detail.trim()) return;


    if (!this.selectedChatId) {
      await this.initializeChat();
    }

    if (!this.selectedChatId) {
      console.error('Failed to initialize chat ID');
      return;
    }

    // Use either the event detail or the component's inputText
    const messageContent = e?.detail || this.inputText.trim();

    const userMessage = {
      role: 'user',
      content: messageContent
    };

    const contextPanel = this.shadowRoot.querySelector('context-panel');
    if (contextPanel) {
      contextPanel.fetchContext(messageContent)
        .catch(error => console.error('Error fetching context:', error));
    }

    this.messages = [...this.messages, userMessage];
    this.inputText = '';  // Clear input after using it
    this.isLoading = true;
    this.waitingForFirstToken = true;

    const assistantMessage = {
      role: 'assistant',
      content: ''
    };
    this.messages = [...this.messages, assistantMessage];

    try {
      // Construct the URL with tutorial context if available
      let chatUrl = `http://localhost:8080/chat/stream?chat_id=${this.selectedChatId}`;

    
      const response = await fetch(chatUrl, {
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

        // Update total steps when receiving assistant message
        const newTotalSteps = this.parseStepCount(assistantMessage);
        if (newTotalSteps > this.currentStepProgress.totalSteps) {
          this.currentStepProgress = {
            ...this.currentStepProgress,
            totalSteps: newTotalSteps
          };
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

  async handleTutorialStart(event) {
    console.log('Tutorial start event received:', event.detail);
    this.currentTutorial = event.detail;
    this.currentTutorialProgress = {
        tutorialId: event.detail.tutorialId,
        currentChapter: 0,
        completedChapters: []
    };
    this.waitingForChapterConfirmation = false;
    this.currentStepProgress = {
        currentStep: event.detail.chapters[0].steps[0].id,
        completedSteps: [],
        lastConfirmation: null,
        totalSteps: 0
    };
    
    try {
        // Get new chat ID
        const response = await fetch('http://localhost:8080/chat/latest/id');
        const data = await response.json();
        this.selectedChatId = (data.id || 0) + 1;
        console.log('Created new chat with ID:', this.selectedChatId);

        const progressResponse = await fetch(
          `http://localhost:8001/progress/${this.selectedChatId}/step/${this.currentStepProgress.currentStep}/0`, 
          {
              method: 'PUT',
              headers: {
                  'Content-Type': 'application/json',
              }
          }
        );

        if (!progressResponse.ok) {
            console.error('Failed to initialize first step progress:', await progressResponse.text());
        }

        let context = null;  // Define context variable in proper scope

        // Initialize progress using current_context endpoint
        const contextResponse = await fetch(
            `http://localhost:8001/current_context/${this.selectedChatId}`
        );

        if (contextResponse.ok) {
            context = await contextResponse.json();  // Assign to scoped variable
            if (context.current_step) {
                // Initialize progress for the first step
                console.log('Initializing first step progress:', {
                    chatId: this.selectedChatId,
                    tutorialId: context.tutorial.id,
                    stepId: context.current_step.id
                });                
            }
        }
        
        this.messages = [];
        this.isLoading = true;
        this.waitingForFirstToken = true;

        const userMessage = {
            role: 'user',
            content: "Let's begin the tutorial."
        };
        
        this.messages = [userMessage];

        // Construct chat URL with context information if available
        let chatUrl = `http://localhost:8080/chat/stream?chat_id=${this.selectedChatId}`;

        const streamResponse = await fetch(chatUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                messages: this.messages,
                temperature: 0.7,
                max_tokens: 2000
            })
        });

        // Create assistant message for streaming response
        const assistantMessage = {
            role: 'assistant',
            content: ''
        };
        this.messages = [...this.messages, assistantMessage];

        const reader = streamResponse.body.getReader();
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
        console.error('Error starting tutorial:', error);
    } finally {
        this.isLoading = false;
        this.waitingForFirstToken = false;
        // Refresh chat list
        const chatHistoryElement = this.shadowRoot.querySelector('chat-history');
        if (chatHistoryElement) {
            chatHistoryElement.loadChats();
        }
    }
  }

  // Add this helper method to handle streaming responses
  async streamResponse(chatUrl, userMessage, assistantMessage) {
    try {
      const response = await fetch(chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          messages: [...this.messages.slice(0, -1), userMessage],
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
      console.error('Error in streamResponse:', error);
    }
  }

  // Add a method to parse step count from assistant messages
  parseStepCount(message) {
    if (message.role === 'assistant') {
      const stepMatch = message.content.match(/Step (\d+):/g);
      if (stepMatch) {
        const steps = stepMatch.map(s => parseInt(s.match(/\d+/)[0]));
        return Math.max(...steps);
      }
    }
    return this.currentStepProgress.totalSteps;
  }

  // Update the tutorial step confirmation handler
  async handleTutorialStepConfirmation(e) {
    const { confirmed } = e.detail;
    this.lastConfirmationResponse = confirmed;
    
    console.log('Tutorial step confirmation:', confirmed);

    if (confirmed) {
        try {
            // Get current context instead of chapter context
            const contextUrl = `http://localhost:8001/current_context/${this.selectedChatId}`;
            console.log('Fetching current context from:', contextUrl);

            const response = await fetch(contextUrl);

            if (response.ok) {
                const context = await response.json();
                console.log('Current context:', context);
                
                const currentStep = context.current_step;
                console.log('Current step to update:', currentStep);
                
                if (currentStep) {
                    // Update progress for this step
                    const progressUrl = `http://localhost:8001/progress/${this.selectedChatId}/step/${currentStep.id}/1`;
                    console.log('Updating progress at:', progressUrl);
                    
                    const progressResponse = await fetch(progressUrl, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });

                    if (!progressResponse.ok) {
                        const errorData = await progressResponse.json();
                        console.error('Failed to update step progress:', {
                            status: progressResponse.status,
                            statusText: progressResponse.statusText,
                            error: errorData
                        });
                    } else {
                        const successData = await progressResponse.json();
                        console.log('Step progress updated successfully:', successData);
                        const chatHistoryElement = this.shadowRoot.querySelector('chat-history');
                        if (chatHistoryElement) {
                          chatHistoryElement.loadChats();
                        }
                    }

                } else {
                    console.log('No current step found in context');
                }
            } else {
                const errorText = await response.text();
                console.error('Failed to fetch current context:', {
                    status: response.status,
                    statusText: response.statusText,
                    error: errorText
                });
            }


        } catch (error) {
            console.error('Error updating step progress:', error);
        }
        
        // Send confirmation to AI
        await this.sendMessage({
            detail: "Yes, I have completed this step."
        });
    } else {
        // If user says no, just send the message without updating progress
        await this.sendMessage({
            detail: "No, I need more help with this step."
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
            @tutorial-step-confirmation=${this.handleTutorialStepConfirmation}
          ></chat-window>
          
          <context-panel></context-panel>
          <learning-panel 
            .chatId=${this.selectedChatId}
            @start-tutorial=${this.handleTutorialStart}
          ></learning-panel>
        </div>
      </div>
    `;
  }
}

customElements.define('llm-assistant-frontend', LlmAssistantFrontend);