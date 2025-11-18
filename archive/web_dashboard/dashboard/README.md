# Betting Dashboard

Responsive Next.js betting dashboard with Notion integration, deployed privately on Vercel.

## Features

- 📊 Real-time betting opportunities dashboard
- 📈 Analytics and performance metrics
- 📝 Notion integration for data synchronization
- 📱 Fully responsive mobile-first design
- 🔒 Private deployment with password protection

## Tech Stack

- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- Recharts (charts)
- Notion SDK
- Vercel deployment

## Getting Started

### Development

```bash
cd dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Environment Variables

Create a `.env.local` file:

```env
NOTION_TOKEN=your_notion_integration_token
```

## Deployment to Vercel

### Prerequisites

1. Vercel account (Pro plan recommended for password protection)
2. Git repository connected to Vercel

### Steps

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Link project**:
   ```bash
   cd dashboard
   vercel link
   ```

4. **Set environment variables**:
   ```bash
   vercel env add NOTION_TOKEN
   ```

5. **Deploy**:
   ```bash
   vercel --prod
   ```

### Password Protection

To enable password protection on Vercel:

1. Go to your project settings on Vercel
2. Navigate to "Deployment Protection"
3. Enable "Password Protection"
4. Set a password for your dashboard

### Private Deployment

The dashboard is configured as private in `vercel.json`. To make it completely private:

1. In Vercel project settings, go to "General"
2. Set "Visibility" to "Private"
3. Only team members with access can view the deployment

## Project Structure

```
dashboard/
├── app/
│   ├── api/          # API routes
│   ├── analytics/    # Analytics page
│   ├── opportunities/ # Opportunities page
│   ├── notion/       # Notion integration page
│   └── settings/     # Settings page
├── components/       # React components
├── lib/             # Utility functions
├── types/           # TypeScript types
└── public/          # Static assets
```

## API Routes

- `/api/opportunities` - Fetch betting opportunities
- `/api/analytics` - Performance metrics
- `/api/analytics/trend` - ROI trend data
- `/api/analytics/sports` - Sport performance
- `/api/matches/live` - Live matches
- `/api/system/status` - System status
- `/api/notion/status` - Notion connection status
- `/api/notion/sync` - Sync opportunities to Notion

## Notion Integration

1. Create a Notion integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Copy the integration token
3. Add it as `NOTION_TOKEN` environment variable
4. Share your Notion databases with the integration
5. Use the Notion page in the dashboard to sync data

## License

MIT

