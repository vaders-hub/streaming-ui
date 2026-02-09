# SSE Streaming UI

Next.js frontend with Server-Sent Events (SSE) streaming support.

## Features

- Next.js 15 with App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Custom SSE hook for real-time data streaming
- pnpm package manager

## Prerequisites

- Node.js 18+
- pnpm

## Setup

1. Install pnpm (if not already installed):
```bash
npm install -g pnpm
```

2. Install dependencies:
```bash
cd front
pnpm install
```

3. Configure environment variables:
```bash
cp .env.example .env.local
# Edit .env.local if needed
```

4. Run the development server:
```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Components

- `StreamingCard` - Reusable card component for SSE streams
- `useSSE` hook - Custom React hook for managing SSE connections
- shadcn/ui components - Button, Card, etc.

## Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint

## Environment Variables

See `.env.example` for all available configuration options.

## Usage

The app connects to the FastAPI backend to receive real-time data streams. Make sure the backend server is running before starting the frontend.
