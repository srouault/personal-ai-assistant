import { css } from 'lit';

export const styles = css`
  :host {
    display: block;
    height: 88vh;
    width: 80%;
    margin: 2rem auto;
    border-radius: 0.75rem;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.3);
    overflow: hidden;
    background-color: #1e1e1e;
    color: #ffffff;
  }

  .flex {
    display: flex;
  }

  .flex-col {
    flex-direction: column;
  }

  .h-full {
    height: 100%;
  }

  .bg-gray-100 {
    background-color: #1e1e1e;
  }

  .message-container {
    height: calc(100% - 80px);
    overflow-y: auto;
    padding: 1rem;
  }

  .message-container::-webkit-scrollbar {
    width: 8px;
  }

  .message-container::-webkit-scrollbar-track {
    background: #1e1e1e;
  }

  .message-container::-webkit-scrollbar-thumb {
    background-color: #404040;
    border-radius: 4px;
  }

  .space-y-4 > * + * {
    margin-top: 1rem;
  }

  .justify-end {
    justify-content: flex-end;
  }

  .justify-start {
    justify-content: flex-start;
  }

  .bg-blue-500 {
    background-color: #0066cc;
  }

  .text-white {
    color: #ffffff;
  }

  .bg-white {
    background-color: #2d2d2d;
  }

  .text-gray-800 {
    color: #ffffff;
  }

  .rounded-lg {
    border-radius: 0.5rem;
  }

  .p-3 {
    padding: 0.75rem;
  }

  .max-w-[80%] {
    max-width: 80%;
  }

  .shadow {
    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.5);
  }

  .whitespace-pre-wrap {
    white-space: pre-wrap;
  }

  .border-t {
    border-top: 1px solid #404040;
  }

  .p-4 {
    padding: 1rem;
  }

  .space-x-4 > * + * {
    margin-left: 1rem;
  }

  textarea {
    flex: 1;
    border: 1px solid #404040;
    border-radius: 0.5rem;
    padding: 0.5rem;
    resize: none;
    height: 40px;
    line-height: 1.5;
    background-color: #2d2d2d;
    color: #ffffff;
  }

  textarea::placeholder {
    color: #808080;
  }

  textarea:focus {
    outline: none;
    border-color: #0066cc;
    box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
  }

  button {
    background-color: #0066cc;
    color: #ffffff;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    border: none;
    cursor: pointer;
    min-width: 80px;
    font-weight: 500;
  }

  button:hover {
    background-color: #0052a3;
  }

  button:focus {
    outline: none;
    box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
  }

  button:disabled {
    background-color: #404040;
    color: #808080;
    cursor: not-allowed;
  }

  .typing-indicator {
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
  }

  .dot {
    width: 8px;
    height: 8px;
    background-color: #0066cc;
    border-radius: 50%;
    margin-right: 4px;
    animation: pulse 1.5s infinite;
    opacity: 0.5;
  }

  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
      opacity: 0.5;
    }
    50% {
      transform: scale(1.2);
      opacity: 1;
    }
  }

  .markdown-body {
    color: inherit;
    padding: 8px 10px;
    border-radius: 5px;
  }

  .markdown-body p {
    margin: 0;
  }

  .markdown-body p:first-child {
    margin-top: 0;
  }

  .markdown-body p:last-child {
    margin-bottom: 0;
  }

  .markdown-body pre {
    margin: 3px 0;
    padding: 10px;
    background-color: #1a1a1a;
    border-radius: 5px;
  }

  .items-center {
    text-align: center;
    width: 100%;
  }


  .relative {
    height: 100%;
  }


  .markdown-body h1,
  .markdown-body h2,
  .markdown-body h3,
  .markdown-body h4,
  .markdown-body h5,
  .markdown-body h6 {
    margin: 0.5rem 0 0.25rem 0;
    font-weight: 600;
    line-height: 1.25;
  }

  .markdown-body h1 { font-size: 1.5em; }
  .markdown-body h2 { font-size: 1.3em; }
  .markdown-body h3 { font-size: 1.2em; }
  .markdown-body h4 { font-size: 1.1em; }
  .markdown-body h5 { font-size: 1em; }
  .markdown-body h6 { font-size: 0.9em; }

  .markdown-body ul,
  .markdown-body ol {
    margin: 0.25rem 0;
    padding-left: 1.5rem;
  }

  .markdown-body li {
    margin: 0.125rem 0;
  }

  .markdown-body blockquote {
    margin: 0.25rem 0;
    padding-left: 1rem;
    border-left: 4px solid #404040;
    color: #808080;
  }

  .markdown-body hr {
    margin: 0.5rem 0;
    border: none;
    border-top: 1px solid #404040;
  }

  .markdown-body table {
    border-collapse: collapse;
    margin: 0.5rem 0;
    width: 100%;
  }

  .markdown-body th,
  .markdown-body td {
    padding: 0.5rem;
    border: 1px solid #404040;
  }

  .markdown-body th {
    background-color: #1a1a1a;
    font-weight: 600;
  }

  .markdown-body a {
    color: #0066cc;
    text-decoration: none;
  }

  .markdown-body a:hover {
    text-decoration: underline;
  }

  .markdown-body img {
    max-width: 100%;
    height: auto;
    border-radius: 0.375rem;
  }

  .p-2 {
    padding: 0.4rem 0.6rem;
  }

  .file-input {
    padding: 0.5rem;
    border: 1px solid #404040;
    border-radius: 0.5rem;
    background-color: #2d2d2d;
    color: #ffffff;
    width: 100%;
  }

  .file-input:hover {
    border-color: #0066cc;
  }
`; 