#!/usr/bin/env node
/**
 * Virtual Camera Pipeline
 * Captures the ChatVRM avatar browser tab via CDP screencast
 * and pipes frames to v4l2loopback virtual webcam (/dev/video10)
 * 
 * Usage: node virtual-camera.js [--fps 30] [--width 1280] [--height 720]
 */

const http = require('http');
const { spawn } = require('child_process');
const WebSocket = require('ws');

const CONFIG = {
  CDP_PORT: 18800,
  V4L2_DEVICE: '/dev/video10',
  FPS: parseInt(process.argv.find((_, i, a) => a[i-1] === '--fps') || '15'),
  WIDTH: parseInt(process.argv.find((_, i, a) => a[i-1] === '--width') || '1280'),
  HEIGHT: parseInt(process.argv.find((_, i, a) => a[i-1] === '--height') || '720'),
  FORMAT: 'jpeg', // jpeg is fastest for CDP screencast
};

async function getTargetWsUrl() {
  return new Promise((resolve, reject) => {
    http.get(`http://127.0.0.1:${CONFIG.CDP_PORT}/json`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const targets = JSON.parse(data);
          const chatvrm = targets.find(t => 
            t.type === 'page' && t.url.includes('localhost:3000')
          );
          if (!chatvrm) {
            reject(new Error('ChatVRM tab not found. Is localhost:3000 open in the managed browser?'));
            return;
          }
          console.log(`📺 Found ChatVRM tab: ${chatvrm.title} (${chatvrm.url})`);
          resolve(chatvrm.webSocketDebuggerUrl);
        } catch (e) {
          reject(e);
        }
      });
    }).on('error', reject);
  });
}

async function startCapture() {
  console.log('🎥 Starting Virtual Camera Pipeline');
  console.log(`   Device: ${CONFIG.V4L2_DEVICE}`);
  console.log(`   Resolution: ${CONFIG.WIDTH}x${CONFIG.HEIGHT}`);
  console.log(`   FPS: ${CONFIG.FPS}`);
  
  // Get CDP WebSocket URL for ChatVRM tab
  const wsUrl = await getTargetWsUrl();
  console.log(`🔌 Connecting to CDP: ${wsUrl}`);
  
  // Start ffmpeg process: reads MJPEG from stdin, outputs to v4l2loopback
  const ffmpeg = spawn('ffmpeg', [
    '-y',
    '-f', 'mjpeg',           // Input: MJPEG stream
    '-framerate', String(CONFIG.FPS),
    '-i', 'pipe:0',          // Read from stdin
    '-vf', `scale=${CONFIG.WIDTH}:${CONFIG.HEIGHT}`,
    '-pix_fmt', 'yuv420p',
    '-f', 'v4l2',            // Output: v4l2 device
    CONFIG.V4L2_DEVICE
  ], {
    stdio: ['pipe', 'pipe', 'pipe']
  });

  ffmpeg.stderr.on('data', (data) => {
    const line = data.toString().trim();
    if (line && !line.startsWith('frame=')) {
      console.log(`[ffmpeg] ${line}`);
    }
  });
  
  ffmpeg.on('close', (code) => {
    console.log(`[ffmpeg] Exited with code ${code}`);
    process.exit(code || 0);
  });

  // Connect to CDP
  const ws = new WebSocket(wsUrl);
  let msgId = 0;
  let frameCount = 0;
  
  function send(method, params = {}) {
    const id = ++msgId;
    ws.send(JSON.stringify({ id, method, params }));
    return id;
  }

  ws.on('open', () => {
    console.log('✅ Connected to CDP');
    
    // Start screencast
    send('Page.startScreencast', {
      format: CONFIG.FORMAT,
      quality: 60,             // Balance quality vs speed
      maxWidth: CONFIG.WIDTH,
      maxHeight: CONFIG.HEIGHT,
      everyNthFrame: 1
    });
    
    console.log('📡 Screencast started. Streaming to virtual camera...');
    console.log('   Press Ctrl+C to stop.');
  });

  ws.on('message', (data) => {
    try {
      const msg = JSON.parse(data);
      
      if (msg.method === 'Page.screencastFrame') {
        const { sessionId, metadata } = msg.params;
        const frameData = Buffer.from(msg.params.data, 'base64');
        
        // Write JPEG frame to ffmpeg stdin
        if (!ffmpeg.stdin.destroyed) {
          ffmpeg.stdin.write(frameData);
        }
        
        // Acknowledge the frame (required to get next frame)
        send('Page.screencastFrameAck', { sessionId });
        
        frameCount++;
        if (frameCount % (CONFIG.FPS * 5) === 0) { // Log every ~5 seconds
          console.log(`📹 Frames captured: ${frameCount} (${metadata.deviceWidth}x${metadata.deviceHeight})`);
        }
      }
    } catch (e) {
      // Ignore parse errors from non-JSON messages
    }
  });

  ws.on('close', () => {
    console.log('❌ CDP connection closed');
    ffmpeg.stdin.end();
  });

  ws.on('error', (err) => {
    console.error('❌ CDP error:', err.message);
  });

  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n🛑 Stopping virtual camera...');
    send('Page.stopScreencast');
    setTimeout(() => {
      ffmpeg.stdin.end();
      ws.close();
      process.exit(0);
    }, 500);
  });

  process.on('SIGTERM', () => {
    ffmpeg.stdin.end();
    ws.close();
    process.exit(0);
  });
}

startCapture().catch((err) => {
  console.error('❌ Failed to start:', err.message);
  process.exit(1);
});
