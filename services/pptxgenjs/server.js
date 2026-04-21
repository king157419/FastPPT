/**
 * FastPPT PptxGenJS Microservice
 * Express server for generating PPTX files from JSON specifications
 */
import express from 'express';
import cors from 'cors';
import pptxgen from 'pptxgenjs';
import { generateSlide } from './generators/teaching.js';
import { getTheme, getLayout } from './generators/templates.js';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));

// Request logging
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.path} - ${res.statusCode} - ${duration}ms`);
  });
  next();
});

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'pptxgenjs-service',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

/**
 * Generate PPTX from JSON specification
 * POST /generate
 * Body: {
 *   teaching_spec: { title, subject, ... },
 *   pages: [ { type, title, ... }, ... ],
 *   theme: 'education' | 'business',
 *   metadata: { author, filename, ... }
 * }
 */
app.post('/generate', async (req, res) => {
  const startTime = Date.now();

  try {
    const { teaching_spec, pages, blocks, theme: themeName, metadata } = req.body;

    // Validation
    if (!pages || !Array.isArray(pages) || pages.length === 0) {
      return res.status(400).json({
        error: 'Invalid request',
        message: 'pages array is required and must not be empty'
      });
    }

    // Initialize presentation
    const pres = new pptxgen();
    const theme = getTheme(themeName || 'education');
    const layout = getLayout('wide');

    // Set presentation properties
    pres.layout = layout.name;
    pres.author = metadata?.author || teaching_spec?.teacher || 'FastPPT AI';
    pres.title = metadata?.title || teaching_spec?.title || '教学课件';
    pres.subject = teaching_spec?.subject || metadata?.subject || '';
    pres.company = 'TeachMind AI';

    // Define master slide with footer
    pres.defineSlideMaster({
      title: 'TEACHING_MASTER',
      background: { color: theme.background },
      objects: [
        {
          rect: {
            x: 0,
            y: 7.2,
            w: '100%',
            h: 0.05,
            fill: { color: theme.primary }
          }
        }
      ]
    });

    // Generate slides
    console.log(`Generating ${pages.length} slides...`);
    for (let i = 0; i < pages.length; i++) {
      const page = pages[i];
      try {
        generateSlide(pres, page, theme);
      } catch (error) {
        console.error(`Error generating slide ${i + 1}:`, error.message);
        // Continue with other slides
      }
    }

    // Generate PPTX buffer
    const buffer = await pres.write({
      outputType: 'nodebuffer',
      compression: true
    });

    const duration = Date.now() - startTime;
    const avgTimePerSlide = duration / pages.length;

    console.log(`Generated PPTX: ${pages.length} slides in ${duration}ms (${avgTimePerSlide.toFixed(0)}ms/slide)`);

    // Set response headers
    const filename = metadata?.filename || `${teaching_spec?.title || 'presentation'}.pptx`;
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.presentationml.presentation');
    res.setHeader('Content-Disposition', `attachment; filename="${encodeURIComponent(filename)}"`);
    res.setHeader('X-Generation-Time', duration);
    res.setHeader('X-Slide-Count', pages.length);

    res.send(buffer);

  } catch (error) {
    console.error('PPTX generation error:', error);
    res.status(500).json({
      error: 'Generation failed',
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
});

/**
 * Get supported slide types
 */
app.get('/slide-types', (req, res) => {
  res.json({
    supported_types: [
      'cover',
      'agenda',
      'content',
      'code',
      'formula',
      'example',
      'two_column',
      'image',
      'quote',
      'summary',
      'animation'
    ],
    block_types: [
      'TextBlock',
      'BulletBlock',
      'CodeBlock',
      'FormulaBlock',
      'CaseBlock',
      'TableBlock',
      'ImageBlock',
      'FlowchartBlock'
    ]
  });
});

/**
 * Get available themes
 */
app.get('/themes', (req, res) => {
  res.json({
    themes: ['education', 'business'],
    default: 'education'
  });
});

/**
 * Error handling middleware
 */
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: err.message
  });
});

/**
 * 404 handler
 */
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    message: `Route ${req.method} ${req.path} not found`
  });
});

// Start server
app.listen(PORT, () => {
  console.log('=================================');
  console.log('FastPPT PptxGenJS Service');
  console.log('=================================');
  console.log(`Server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Generate endpoint: POST http://localhost:${PORT}/generate`);
  console.log('=================================');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully...');
  process.exit(0);
});
