const express = require('express');
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 8080;

// Start Flask app in background
let flaskProcess;

function startFlaskApp() {
  console.log('Starting Flask application...');
  flaskProcess = spawn(process.env.PYTHON_EXECUTABLE || 'python3', ['app.py'], {
    cwd: __dirname,
    env: { ...process.env, PORT: '5000' },
    stdio: ['inherit', 'pipe', 'pipe']
  });

  flaskProcess.stdout.on('data', (data) => {
    console.log(`Flask: ${data}`);
  });

  flaskProcess.stderr.on('data', (data) => {
    console.error(`Flask Error: ${data}`);
  });

  flaskProcess.on('close', (code) => {
    console.log(`Flask process exited with code ${code}`);
  });
}

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"],
      fontSrc: ["'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com"],
      scriptSrc: ["'self'", "'unsafe-inline'", "https://www.gstatic.com", "https://cdn.jsdelivr.net"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
}));

// Enable CORS
app.use(cors());

// Parse JSON bodies
app.use(express.json());

// Serve static files from Flask static directory
app.use('/static', express.static('static'));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    service: 'VibeCheck Flask App',
    version: '1.0.0',
    flask_status: flaskProcess ? 'running' : 'stopped'
  });
});

// Proxy all other requests to Flask
app.use('*', async (req, res) => {
  try {
    const flaskUrl = `http://localhost:5000${req.originalUrl}`;
    const fetch = (await import('node-fetch')).default;
    
    const response = await fetch(flaskUrl, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        ...req.headers
      },
      body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined
    });

    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      res.status(response.status).json(data);
    } else {
      const text = await response.text();
      res.status(response.status).send(text);
    }
  } catch (error) {
    console.error('Proxy error:', error);
    res.status(500).send(`
      <!DOCTYPE html>
      <html>
      <head><title>VibeCheck - Starting Up</title></head>
      <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🚀 VibeCheck is Starting Up</h1>
        <p>Flask application is initializing... Please wait a moment and refresh.</p>
        <p><a href="/">Refresh Page</a></p>
      </body>
      </html>
    `);
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// Start Flask first, then Express
startFlaskApp();

// Give Flask time to start before starting Express
setTimeout(() => {
  app.listen(PORT, () => {
    console.log(`🚀 VibeCheck proxy server running on port ${PORT}`);
    console.log(`📱 Flask app proxied from localhost:5000`);
  });
}, 2000);

// Cleanup on exit
process.on('SIGTERM', () => {
  if (flaskProcess) {
    flaskProcess.kill();
  }
});

process.on('SIGINT', () => {
  if (flaskProcess) {
    flaskProcess.kill();
  }
  process.exit();
});

// Start server
