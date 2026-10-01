# HandyFont — Frontend

React + Vite frontend for HandyFont. See the [project README](../README.md) for full documentation.

## Quick Start

```bash
npm install
npm run dev
```

Runs at `http://localhost:5173`. Expects the backend API at `http://localhost:8000`.

## Pages

| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | `Upload.jsx` | Download template & upload filled scan |
| `/editor` | `Editor.jsx` | Enter text, pick paper style & pen color |
| `/preview` | `Preview.jsx` | View rendered output & export PNG/PDF |

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | Production build to `dist/` |
| `npm run lint` | Run Oxlint |
| `npm run preview` | Preview production build locally |
