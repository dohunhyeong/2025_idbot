# Busan Chatbot Frontend

A React 19 + Vite chatbot frontend that communicates with a local backend server.

## Project Structure

```
src/
├── api/
│   └── api.js              # All backend API calls (BASE_URL defined here)
├── components/
│   ├── ChatContainer.jsx   # Chat message list container
│   ├── Footer.jsx          # Footer component
│   ├── Message.jsx         # Individual message bubble (markdown rendering)
│   └── QueryInput.jsx      # User text input and submit
├── pages/
│   ├── ChatPage.jsx        # Main chatbot UI (route: /)
│   ├── AdminPage.jsx       # Log viewer, token-gated (route: /admin)
│   └── PopupPage.jsx       # Update notice popup (route: /popup)
├── styles/
│   ├── chat.css            # Chat UI styles (responsive: 1024px, 768px, 480px)
│   ├── admin.css           # Admin table styles
│   └── index.css           # Global resets
├── App.jsx                 # Router setup (3 routes)
└── main.jsx                # React entry point
```

## Routes

| Route | Page | Purpose |
|-------|------|---------|
| `/` | `ChatPage` | Main chatbot UI |
| `/admin` | `AdminPage` | Log viewer (requires admin token) |
| `/popup` | `PopupPage` | Update notice popup |

## Getting Started

### Prerequisites

- Node.js 18+
- A backend server running and accessible (default: `http://localhost:8000` via Vite proxy)

### Install & Run

```bash
npm install
npm run dev       # Dev server at http://localhost:5173
npm run build     # Production build → dist/
npm run preview   # Preview production build locally
npm run lint      # Run ESLint
```

## Backend Server Configuration

`BASE_URL` is read from the environment variable **`VITE_API_BASE_URL`**. If the variable is not set, it defaults to an empty string (relative paths), which means all requests go through the **Vite dev proxy**.

```js
// src/api/api.js
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';
```

### Option 1: Use the Vite dev proxy (default, recommended for local dev)

Leave `VITE_API_BASE_URL` unset. Update the proxy target in `vite.config.js` if your backend runs on a different address:

```js
// vite.config.js
server: {
  proxy: {
    '/query': 'http://localhost:8000',  // ← change this
    '/admin': 'http://localhost:8000',  // ← and this
  },
},
```

### Option 2: Set an explicit backend URL via environment variable

Create a `.env.local` file in the project root:

```env
VITE_API_BASE_URL=http://192.168.1.100:8000
# or
VITE_API_BASE_URL=https://api.example.com
```

> **Summary**: For local development, just update the proxy target in `vite.config.js`. For production or remote backends, set `VITE_API_BASE_URL`.

## API Endpoints Expected

The frontend expects the backend to expose:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/query` | Send a chat query |
| `GET` | `/admin/logs?limit=N` | Fetch recent logs |
| `GET` | `/admin/logs/search?q=...&limit=N` | Search logs |
| `GET` | `/admin/logs/:id` | Fetch a single log detail |

Admin endpoints require an `X-ADMIN-TOKEN` header.

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `react` 19 | UI framework |
| `react-router-dom` 7 | Client-side routing |
| `react-markdown` + `remark-gfm` | Render bot responses as Markdown |
