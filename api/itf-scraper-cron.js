// Vercel Cron Job for ITF Scraper
// Runs 2x per day at 08:00 and 20:00 EET (06:00 and 18:00 UTC)
// Vercel Cron will call this endpoint automatically

const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

export default async function handler(req, res) {
  // Verify this is called by Vercel Cron
  const authHeader = req.headers.authorization;
  const cronSecret = process.env.CRON_SECRET || process.env.VERCEL_CRON_SECRET;
  
  if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  console.log('🚀 ITF Scraper Cron started at', new Date().toISOString());

  try {
    // Use Python from system or Vercel environment
    const pythonCmd = process.env.PYTHON_PATH || 'python3';
    const projectRoot = process.cwd();
    
    // Run the scraper
    const { stdout, stderr } = await execAsync(
      `cd ${projectRoot} && ${pythonCmd} run_itf_scraper.py`,
      { 
        maxBuffer: 10 * 1024 * 1024, // 10MB buffer
        timeout: 300000, // 5 minutes timeout
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1'
        }
      }
    );

    console.log('✅ ITF Scraper completed successfully');
    console.log('Output:', stdout.substring(0, 500)); // First 500 chars

    return res.status(200).json({
      success: true,
      timestamp: new Date().toISOString(),
      message: 'ITF scraper executed successfully',
      output_preview: stdout.substring(0, 500),
      has_errors: stderr.length > 0
    });
  } catch (error) {
    console.error('❌ ITF Scraper Cron Error:', error);
    return res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
      stderr: error.stderr?.substring(0, 500)
    });
  }
}
