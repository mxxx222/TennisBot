# Vercel Deployment Guide

## Quick Deploy

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Go to [vercel.com](https://vercel.com)** and sign in
2. **Click "Add New Project"**
3. **Import your Git repository** (TennisBot)
4. **Configure project:**
   - Framework Preset: **Next.js**
   - Root Directory: **dashboard**
   - Build Command: `npm run build` (auto-detected)
   - Output Directory: `.next` (auto-detected)
5. **Add Environment Variables:**
   - `NOTION_TOKEN` - Your Notion integration token
6. **Click "Deploy"**

### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI (if not installed)
npm i -g vercel

# Navigate to dashboard directory
cd dashboard

# Login to Vercel
vercel login

# Deploy (first time - will ask questions)
vercel

# Deploy to production
vercel --prod
```

## Environment Variables

Set these in Vercel Dashboard → Project Settings → Environment Variables:

- `NOTION_TOKEN` - Notion integration token (required for Notion sync)

## Password Protection

To enable password protection (Vercel Pro required):

1. Go to your project on Vercel
2. Navigate to **Settings** → **Deployment Protection**
3. Enable **Password Protection**
4. Set a password
5. Save

## Private Deployment

To make the dashboard completely private:

1. Go to **Settings** → **General**
2. Set **Visibility** to **Private**
3. Only team members with access can view

## Post-Deployment

After deployment:

1. **Test the dashboard** at your Vercel URL
2. **Configure Notion integration:**
   - Create integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
   - Copy token and add to Vercel environment variables
   - Share your Notion databases with the integration
3. **Enable password protection** (if using Vercel Pro)

## Troubleshooting

### Build Fails

- Check that `package.json` has all dependencies
- Verify Node.js version (18+ recommended)
- Check build logs in Vercel dashboard

### Notion Integration Not Working

- Verify `NOTION_TOKEN` is set in environment variables
- Check that integration has access to your databases
- Review API route logs in Vercel dashboard

### API Routes Not Working

- Check that API routes are in `app/api/` directory
- Verify route handlers export correct functions (GET, POST, etc.)
- Check Vercel function logs

## Next Steps

1. ✅ Code pushed to Git
2. ✅ Deploy to Vercel
3. ⏳ Set environment variables
4. ⏳ Enable password protection
5. ⏳ Configure Notion integration
6. ⏳ Test all features

