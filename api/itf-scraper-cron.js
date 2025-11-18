// Vercel Cron Job for ITF Scraper
// Runs 2x per day at 08:00 and 20:00 EET (06:00 and 18:00 UTC)
// Vercel Cron will call this endpoint automatically
// This endpoint calls an external service or uses HTTP to trigger the Python script

const https = require('https');
const http = require('http');

export default async function handler(req, res) {
  // Verify this is called by Vercel Cron (optional security)
  const authHeader = req.headers.authorization;
  const cronSecret = process.env.CRON_SECRET || process.env.VERCEL_CRON_SECRET;
  
  if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  console.log('🚀 ITF Scraper Cron started at', new Date().toISOString());

  try {
    // Option 1: Call external service (if you have one running)
    // Option 2: Use Vercel's serverless function to call Python
    // For now, we'll use a simple HTTP call to trigger the scraper
    
    // Since Vercel doesn't support Python directly, we need to:
    // 1. Use an external service (Render, Railway, etc.) to run Python
    // 2. OR use Vercel's build command to install Python (not recommended)
    // 3. OR rewrite the scraper logic in Node.js
    
    // For Vercel Pro, the best approach is to:
    // - Keep the Python script running on a separate service
    // - Call it via HTTP from this cron endpoint
    
    const scraperUrl = process.env.ITF_SCRAPER_URL || 'https://your-python-service.com/run-scraper';
    
    // Make HTTP request to Python service
    const response = await fetch(scraperUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.SCRAPER_API_KEY || ''}`
      },
      body: JSON.stringify({
        action: 'run_itf_scraper',
        timestamp: new Date().toISOString()
      })
    });

    const result = await response.json();

    console.log('✅ ITF Scraper triggered successfully');

    return res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      message: 'ITF scraper triggered successfully',
      result: result
    });
  } catch (error) {
    console.error('❌ ITF Scraper Cron Error:', error);
    return res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
      note: 'Make sure ITF_SCRAPER_URL is set in Vercel environment variables'
    });
  }
}
