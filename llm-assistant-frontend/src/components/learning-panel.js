import { LitElement, html, css } from 'lit';
import { marked } from 'marked';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';

export class LearningPanel extends LitElement {
  static properties = {
    query: { type: String },
    isVisible: { type: Boolean },
    contexts: { type: Array },
    selectedContext: { type: Object },
    learningPaths: { type: Array },
    selectedPath: { type: Object },
    tutorials: { type: Array }
  };

  constructor() {
    super();
    this.query = '';
    this.isVisible = false;
    this.contexts = [];
    this.selectedContext = null;
    this.learningPaths = [];
    this.selectedPath = null;
    this.tutorials = [];
  }

  static styles = css`
    :host {
      position: fixed;
      right: 0;
      top: 0;
      height: 100vh;
      z-index: 50;
      pointer-events: none;
    }

    .backdrop {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(0, 0, 0, 0);
      transition: background-color 0.3s ease;
      pointer-events: none;
      z-index: 40;
    }

    .backdrop.visible {
      background-color: rgba(0, 0, 0, 0.5);
      pointer-events: auto;
    }

    .panel-wrapper {
      height: 100%;
      position: relative;
      z-index: 50;
    }

    .panel-container {
      width: 320px;
      height: 100vh;
      transform: translateX(100%);
      transition: transform 0.3s ease;
      background-color: #2d2d2d;
      border-radius: 0 0 4px 4px;
      box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
      border-left: 1px solid #111;
      display: flex;
      flex-direction: column;
      pointer-events: auto;
    }

    .panel-container.visible {
      transform: translateX(0);
    }

    .panel-header {
      flex: 0 0 auto;
      border-bottom: 1px solid #e5e7eb;
      background-color: #222;
    }

    .panel-content {
      flex: 1 1 auto;
      overflow-y: auto;
      padding: 1rem;
    }

    .context-items {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .toggle-button {
      position: absolute;
      left: -40px;
      width: 40px;
      height: 120px;
      top: 121px;
      writing-mode: vertical-rl;
      text-orientation: mixed;
      transform: rotate(0deg);
      background-color: rgb(147, 51, 234);
      color: white;
      border: none;
      cursor: pointer;
      border-radius: 4px 0 0 4px;
      transition: background-color 0.2s;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 8px 0;
      pointer-events: auto;
    }

    .toggle-button:hover {
      background-color: rgb(126, 34, 206);
    }

    .toggle-button:focus {
      outline: none;
      ring: 2px;
      ring-color: rgb(147, 51, 234);
    }

    .title-text {
      text-align: center;
      padding: 10px;
      background-color: #222;
    }
    
    .text-context {
        padding: 10px;
    }

    .metadata-container {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      padding-top: 0.75rem;
      margin-top: 0.75rem;
      border-top: 1px solid #e5e7eb;
      font-size: 0.75rem;
      color: #6b7280;
    }

    .metadata-item {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      min-width: fit-content;
    }

    .source-item {
      flex: 1 1 100%;
    }

    .metrics-container {
      display: flex;
      gap: 0.75rem;
      justify-content: space-between;
      width: 100%;
    }

    .metadata-label {
      font-weight: 500;
      color: #4b5563;
    }

    .metadata-value {
      color: #6b7280;
    }

    .relevance-badge {
      padding: 0.25rem 0.5rem;
      border-radius: 9999px;
      font-weight: 500;
      text-transform: capitalize;
    }

    .relevance-high {
      background-color: #dcfce7;
      color: #166534;
    }

    .relevance-medium {
      background-color: #fef9c3;
      color: #854d0e;
    }

    .relevance-low {
      background-color: #fee2e2;
      color: #991b1b;
    }

    .arrow-icon {
      display: inline-block;
      transform: rotate(90deg);
      font-size: 16px;
      font-weight: bold;
    }

    .button-text {
      writing-mode: vertical-rl;
      text-orientation: mixed;
    }

    .context-item {
      cursor: pointer;
    }

    .full-document-view {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.75);
      z-index: 100;
      padding: 2rem;
      overflow-y: auto;
      display: none;
      pointer-events: auto;
    }

    .full-document-view.visible {
      display: block;
    }

    .document-content {
      background-color: #2d2d2d;
      padding: 2rem;
      border-radius: 0.5rem;
      max-width: 800px;
      margin: 0 auto;
      position: relative;
      border: 1px solid #e5e7eb;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
      z-index: 101;
    }

    .document-content h2 {
      color: #fafafa;
      font-size: 1.25rem;
      font-weight: 600;
      margin-bottom: 1rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid #e5e7eb;
    }

    .document-content .content-text {
      color: #fff;
      line-height: 1.625;
      font-size: 0.875rem;
    }

    .close-button {
      position: absolute;
      top: 1rem;
      right: 1rem;
      background: none;
      border: none;
      font-size: 1.5rem;
      cursor: pointer;
      color: #4b5563;
      width: 2rem;
      height: 2rem;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 0.375rem;
      transition: all 0.2s;
    }

    .close-button:hover {
      background-color: #f3f4f6;
      color: #1f2937;
    }

    .markdown-content {
      color: #fff;
    }

    .markdown-content h1,
    .markdown-content h2,
    .markdown-content h3,
    .markdown-content h4,
    .markdown-content h5,
    .markdown-content h6 {
      margin-top: 1.5em;
      margin-bottom: 0.75em;
      font-weight: 600;
    }

    .markdown-content p {
      margin-bottom: 1em;
      line-height: 1.625;
    }

    .markdown-content code {
      background: #1a1a1a;
      padding: 0.2em 0.4em;
      border-radius: 3px;
      font-family: 'Fira Code', monospace;
      font-size: 0.9em;
    }

    .markdown-content pre {
      background: #1a1a1a;
      padding: 1em;
      border-radius: 4px;
      overflow-x: auto;
      margin: 1em 0;
    }

    .markdown-content pre code {
      background: none;
      padding: 0;
      border-radius: 0;
    }

    .markdown-content ul,
    .markdown-content ol {
      margin: 1em 0;
      padding-left: 2em;
    }

    .markdown-content li {
      margin: 0.5em 0;
    }

    .markdown-content blockquote {
      border-left: 4px solid #4b5563;
      padding-left: 1em;
      margin: 1em 0;
      color: #9ca3af;
    }

    .markdown-content a {
      color: #60a5fa;
      text-decoration: underline;
    }

    .markdown-content a:hover {
      color: #93c5fd;
    }

    .markdown-content table {
      border-collapse: collapse;
      width: 100%;
      margin: 1em 0;
    }

    .markdown-content th,
    .markdown-content td {
      border: 1px solid #4b5563;
      padding: 0.5em;
    }

    .markdown-content th {
      background: #1a1a1a;
    }

    .learning-paths-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .learning-path-item {
      padding: 1rem;
      background: #333;
      border-radius: 0.5rem;
      cursor: pointer;
      transition: background-color 0.2s;
    }

    .learning-path-item:hover {
      background: #444;
    }

    .path-title {
      color: #fff;
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }

    .path-description {
      color: #ccc;
      font-size: 0.9rem;
      margin-bottom: 0.5rem;
    }

    .path-metadata {
      display: flex;
      gap: 0.5rem;
      font-size: 0.8rem;
    }

    .category {
      background: #2563eb;
      color: white;
      padding: 0.2rem 0.5rem;
      border-radius: 9999px;
    }

    .back-button {
      background: none;
      border: none;
      color: #60a5fa;
      cursor: pointer;
      padding: 0.5rem 0;
      margin-bottom: 1rem;
      font-size: 0.9rem;
    }

    .back-button:hover {
      color: #93c5fd;
    }

    .tutorials-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      margin-top: 1rem;
    }

    .tutorial-item {
      padding: 1rem;
      background: #333;
      border-radius: 0.5rem;
      cursor: pointer;
      transition: background-color 0.2s;
    }

    .tutorial-item:hover {
      background: #444;
    }

    .tutorial-title {
      color: #fff;
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }

    .tutorial-description {
      color: #ccc;
      font-size: 0.9rem;
      margin-bottom: 0.5rem;
    }

    .tutorial-metadata {
      color: #9ca3af;
      font-size: 0.8rem;
    }

    .content-text {
      margin-top: 1rem;
      line-height: 1.6;
    }

    .metadata-container {
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid #444;
    }

    .metadata-item {
      display: flex;
      gap: 0.5rem;
      color: #9ca3af;
      font-size: 0.9rem;
    }

    .metadata-label {
      font-weight: 500;
    }
  `;

  togglePanel() {
    this.isVisible = !this.isVisible;
    if (this.isVisible) {
      this.dispatchEvent(new CustomEvent('panel-opened'));
    }
  }

  async fetchContext(query) {
    try {
      const response = await fetch('http://localhost:8001/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: query,
          num_results: 3,
          min_similarity: 0.25
        })
      });

      const data = await response.json();
      
      // Deduplicate results based on source file and keep highest similarity match
      const sourceMap = new Map();
      data.results.forEach(result => {
        const source = result.metadata.source;
        if (!sourceMap.has(source) || sourceMap.get(source).metadata.similarity < result.metadata.similarity) {
          sourceMap.set(source, result);
        }
      });

      // Convert back to array and sort by similarity
      this.contexts = Array.from(sourceMap.values())
        .sort((a, b) => b.metadata.similarity - a.metadata.similarity)
        .map(result => ({
          text: result.text,
          source: result.metadata.source,
          similarity: result.metadata.similarity,
          relevance: result.metadata.relevance,
          fullDocument: result.metadata.full_document
        }));

    } catch (error) {
      console.error('Error fetching context:', error);
    }
  }

  showFullDocument(context) {
    this.selectedContext = context;
  }

  closeDocument() {
    this.selectedContext = null;
  }

  async fetchLearningPaths() {
    try {
      const response = await fetch('http://localhost:8001/learning-paths');
      const data = await response.json();
      this.learningPaths = data;
    } catch (error) {
      console.error('Error fetching learning paths:', error);
    }
  }

  async fetchTutorials(pathId) {
    try {
      const response = await fetch(`http://localhost:8001/learning-paths/${pathId}/tutorials`);
      const data = await response.json();
      this.tutorials = data;
    } catch (error) {
      console.error('Error fetching tutorials:', error);
    }
  }

  async selectPath(path) {
    this.selectedPath = path;
    await this.fetchTutorials(path.id);
  }

  async selectTutorial(tutorial) {
    this.selectedContext = {
      title: tutorial.title,
      content: tutorial.content,
      metadata: {
        duration: tutorial.estimated_duration,
        created_at: tutorial.created_at
      }
    };
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchLearningPaths();
  }

  render() {
    return html`
      <div class="backdrop ${this.isVisible ? 'visible' : ''}" 
           @click=${() => this.togglePanel()}>
      </div>
      <div class="panel-wrapper">
        <div class="full-document-view ${this.selectedContext ? 'visible' : ''}"
             @click=${(e) => e.target === e.currentTarget && this.closeDocument()}>
          <div class="document-content">
            <button class="close-button" @click=${this.closeDocument}>&times;</button>
            ${this.selectedContext ? html`
              <h2>${this.selectedContext.title}</h2>
              <div class="content-text markdown-content">
                ${unsafeHTML(marked.parse(this.selectedContext.content))}
              </div>
              <div class="metadata-container">
                <div class="metadata-item">
                  <span class="metadata-label">Duration:</span>
                  <span class="metadata-value">${this.selectedContext.metadata.duration} min</span>
                </div>
              </div>
            ` : ''}
          </div>
        </div>

        <div class="panel-container ${this.isVisible ? 'visible' : ''} bg-white shadow-lg">
          <button
            @click=${this.togglePanel}
            class="toggle-button"
          >
            <span class="arrow-icon">
              ${this.isVisible ? '\u2190' : '\u2192'}
            </span>
            <span class="button-text">Learning</span>
          </button>

          <div class="panel-header">
            <h3 class="text-lg font-semibold text-gray-700 title-text">Learning Paths</h3>
          </div>

          <div class="panel-content">
            ${this.selectedPath ? 
              html`
                <div class="selected-path">
                  <button 
                    @click=${() => this.selectedPath = null}
                    class="back-button"
                  >
                    ← Back to Learning Paths
                  </button>
                  <h4 class="path-title">${this.selectedPath.title}</h4>
                  <p class="path-description">${this.selectedPath.description}</p>
                  
                  <div class="tutorials-list">
                    ${this.tutorials.map(tutorial => html`
                      <div class="tutorial-item" @click=${() => this.selectTutorial(tutorial)}>
                        <h5 class="tutorial-title">${tutorial.title}</h5>
                        <p class="tutorial-description">${tutorial.description}</p>
                        <div class="tutorial-metadata">
                          <span class="duration">Duration: ${tutorial.estimated_duration} min</span>
                        </div>
                      </div>
                    `)}
                  </div>
                </div>
              ` : 
              html`
                <div class="learning-paths-list">
                  ${this.learningPaths.map(path => html`
                    <div 
                      class="learning-path-item"
                      @click=${() => this.selectPath(path)}
                    >
                      <h4 class="path-title">${path.title}</h4>
                      <p class="path-description">${path.description}</p>
                      <div class="path-metadata">
                        <span class="category">${path.category}</span>
                      </div>
                    </div>
                  `)}
                </div>
              `
            }
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('learning-panel', LearningPanel); 