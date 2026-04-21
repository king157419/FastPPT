/**
 * Teaching slide generators supporting 11 block types from slide_blocks.py
 */
import pptxgen from 'pptxgenjs';
import { getTheme } from './templates.js';

/**
 * Generate cover/title slide
 */
export function generateCoverSlide(pres, page, theme) {
  const slide = pres.addSlide();

  slide.background = { color: theme.background };

  // Main title
  const title = page.title || '';
  slide.addText(title, {
    x: 0.5,
    y: '35%',
    w: '90%',
    h: 1.5,
    fontSize: 44,
    bold: true,
    color: theme.primary,
    align: 'center',
    fontFace: theme.fonts.title,
    lang: 'zh-CN'
  });

  // Subtitle
  const subtitle = page.subtitle || '';
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5,
      y: '50%',
      w: '90%',
      h: 0.8,
      fontSize: 24,
      color: theme.text,
      align: 'center',
      fontFace: theme.fonts.body,
      lang: 'zh-CN'
    });
  }

  // Date
  const date = new Date().toLocaleDateString('zh-CN');
  slide.addText(date, {
    x: 0.5,
    y: '85%',
    w: '90%',
    fontSize: 14,
    color: theme.text,
    align: 'center'
  });
}

/**
 * Generate agenda/table of contents slide
 */
export function generateAgendaSlide(pres, page, theme) {
  const slide = pres.addSlide();

  // Title
  slide.addText(page.title || '目录', {
    x: 0.5,
    y: 0.5,
    w: 9.0,
    h: 0.75,
    fontSize: 36,
    bold: true,
    color: theme.primary,
    fontFace: theme.fonts.title,
    lang: 'zh-CN'
  });

  // Separator line
  slide.addShape(pres.ShapeType.rect, {
    x: 0.5,
    y: 1.3,
    w: 9.0,
    h: 0.05,
    fill: { color: theme.secondary }
  });

  // Agenda items
  const items = page.items || page.points || [];
  if (items.length > 0) {
    slide.addText(items.join('\n'), {
      x: 1.5,
      y: 1.8,
      w: 7.5,
      h: 4.5,
      fontSize: 20,
      bullet: { type: 'number' },
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN',
      lineSpacing: 36
    });
  }
}

/**
 * Generate content slide with bullets
 */
export function generateContentSlide(pres, page, theme) {
  const slide = pres.addSlide();

  // Title
  slide.addText(page.title || '', {
    x: 0.5,
    y: 0.5,
    w: 9.0,
    h: 0.75,
    fontSize: 32,
    bold: true,
    color: theme.primary,
    fontFace: theme.fonts.title,
    lang: 'zh-CN'
  });

  // Separator line
  slide.addShape(pres.ShapeType.rect, {
    x: 0.5,
    y: 1.3,
    w: 9.0,
    h: 0.05,
    fill: { color: theme.secondary }
  });

  // Bullet points
  const bullets = page.bullets || [];
  if (bullets.length > 0) {
    slide.addText(bullets.join('\n'), {
      x: 1.0,
      y: 1.8,
      w: 8.5,
      h: 4.5,
      fontSize: 18,
      bullet: { type: 'bullet' },
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN',
      lineSpacing: 30
    });
  }

  // Teaching tip (footer)
  const tip = page.tip;
  if (tip) {
    slide.addText(`💡 ${tip}`, {
      x: 0.5,
      y: 6.8,
      w: 9.0,
      fontSize: 12,
      color: theme.accent,
      fontFace: theme.fonts.body,
      lang: 'zh-CN',
      italic: true
    });
  }
}

/**
 * Generate code slide
 */
export function generateCodeSlide(pres, page, theme) {
  const slide = pres.addSlide();

  // Title
  slide.addText(page.title || '', {
    x: 0.5,
    y: 0.5,
    w: 9.0,
    h: 0.75,
    fontSize: 28,
    bold: true,
    color: theme.primary,
    fontFace: theme.fonts.title,
    lang: 'zh-CN'
  });

  // Code block
  const code = page.code || '';
  if (code) {
    slide.addText(code, {
      x: 0.5,
      y: 1.5,
      w: 9.0,
      h: 3.5,
      fontSize: 14,
      fontFace: theme.fonts.code,
      color: '000000',
      fill: theme.lightBg,
      align: 'left',
      valign: 'top'
    });
  }

  // Explanation
  const explanation = page.explanation || '';
  if (explanation) {
    slide.addText(explanation, {
      x: 0.5,
      y: 5.2,
      w: 9.0,
      fontSize: 14,
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN'
    });
  }
}

/**
 * Generate formula slide
 */
export function generateFormulaSlide(pres, page, theme) {
  const slide = pres.addSlide();

  // Title
  slide.addText(page.title || '', {
    x: 0.5,
    y: 0.5,
    w: 9.0,
    h: 0.75,
    fontSize: 28,
    bold: true,
    color: theme.primary,
    fontFace: theme.fonts.title,
    lang: 'zh-CN'
  });

  // Formulas (display as text for now, LaTeX rendering would need additional processing)
  const formulas = page.formulas || [];
  if (formulas.length > 0) {
    const formulaText = formulas.map(f => typeof f === 'string' ? f : f.latex || f.text || '').join('\n\n');
    slide.addText(formulaText, {
      x: 1.0,
      y: 1.8,
      w: 8.0,
      h: 2.5,
      fontSize: 20,
      color: theme.text,
      fontFace: theme.fonts.code,
      align: 'center',
      valign: 'middle',
      fill: theme.lightBg
    });
  }

  // Explanation
  const explanation = page.explanation || '';
  if (explanation) {
    slide.addText(explanation, {
      x: 0.5,
      y: 4.8,
      w: 9.0,
      fontSize: 16,
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN'
    });
  }
}

/**
 * Generate example/case slide
 */
export function generateExampleSlide(pres, page, theme) {
  const slide = pres.addSlide();

  // Title
  slide.addText(page.title || '', {
    x: 0.5,
    y: 0.5,
    w: 9.0,
    h: 0.75,
    fontSize: 28,
    bold: true,
    color: theme.primary,
    fontFace: theme.fonts.title,
    lang: 'zh-CN'
  });

  let yPos = 1.5;

  // Problem
  const problem = page.problem || '';
  if (problem) {
    slide.addText('问题：', {
      x: 0.5,
      y: yPos,
      w: 9.0,
      fontSize: 16,
      bold: true,
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN'
    });
    yPos += 0.4;

    slide.addText(problem, {
      x: 0.5,
      y: yPos,
      w: 9.0,
      fontSize: 14,
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN'
    });
    yPos += 0.8;
  }

  // Steps
  const steps = page.steps || [];
  if (steps.length > 0) {
    slide.addText('解题步骤：', {
      x: 0.5,
      y: yPos,
      w: 9.0,
      fontSize: 16,
      bold: true,
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN'
    });
    yPos += 0.4;

    slide.addText(steps.join('\n'), {
      x: 1.0,
      y: yPos,
      w: 8.5,
      fontSize: 14,
      bullet: { type: 'number' },
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN',
      lineSpacing: 28
    });
    yPos += steps.length * 0.4 + 0.4;
  }

  // Answer
  const answer = page.answer || '';
  if (answer) {
    slide.addText('答案：', {
      x: 0.5,
      y: yPos,
      w: 9.0,
      fontSize: 16,
      bold: true,
      color: theme.accent,
      fontFace: theme.fonts.body,
      lang: 'zh-CN'
    });
    yPos += 0.4;

    slide.addText(answer, {
      x: 0.5,
      y: yPos,
      w: 9.0,
      fontSize: 14,
      color: theme.accent,
      fontFace: theme.fonts.body,
      lang: 'zh-CN'
    });
  }
}

/**
 * Generate two-column comparison slide
 */
export function generateTwoColumnSlide(pres, page, theme) {
  const slide = pres.addSlide();

  // Title
  slide.addText(page.title || '', {
    x: 0.5,
    y: 0.5,
    w: 9.0,
    h: 0.75,
    fontSize: 28,
    bold: true,
    color: theme.primary,
    fontFace: theme.fonts.title,
    lang: 'zh-CN'
  });

  const left = page.left || {};
  const right = page.right || {};

  // Left column
  if (left.title) {
    slide.addText(left.title, {
      x: 0.5,
      y: 1.5,
      w: 4.25,
      fontSize: 20,
      bold: true,
      color: theme.secondary,
      fontFace: theme.fonts.body,
      lang: 'zh-CN'
    });
  }

  if (left.items && left.items.length > 0) {
    slide.addText(left.items.join('\n'), {
      x: 0.5,
      y: 2.0,
      w: 4.25,
      fontSize: 14,
      bullet: true,
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN',
      lineSpacing: 28
    });
  }

  // Divider
  slide.addShape(pres.ShapeType.rect, {
    x: 5.0,
    y: 1.5,
    w: 0.05,
    h: 4.5,
    fill: { color: theme.secondary }
  });

  // Right column
  if (right.title) {
    slide.addText(right.title, {
      x: 5.25,
      y: 1.5,
      w: 4.25,
      fontSize: 20,
      bold: true,
      color: theme.accent,
      fontFace: theme.fonts.body,
      lang: 'zh-CN'
    });
  }

  if (right.items && right.items.length > 0) {
    slide.addText(right.items.join('\n'), {
      x: 5.25,
      y: 2.0,
      w: 4.25,
      fontSize: 14,
      bullet: true,
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN',
      lineSpacing: 28
    });
  }
}

/**
 * Generate image slide
 */
export function generateImageSlide(pres, page, theme) {
  const slide = pres.addSlide();

  // Title
  slide.addText(page.title || '', {
    x: 0.5,
    y: 0.5,
    w: 9.0,
    h: 0.75,
    fontSize: 28,
    bold: true,
    color: theme.primary,
    fontFace: theme.fonts.title,
    lang: 'zh-CN'
  });

  // Image
  const imageData = page.image_base64 || page.image_url;
  if (imageData) {
    const imageOptions = {
      x: 1.5,
      y: 1.5,
      w: 7.0,
      h: 4.0
    };

    if (page.image_base64) {
      imageOptions.data = page.image_base64;
    } else if (page.image_url) {
      imageOptions.path = page.image_url;
    }

    slide.addImage(imageOptions);
  }

  // Caption
  const caption = page.caption || '';
  if (caption) {
    slide.addText(caption, {
      x: 0.5,
      y: 6.0,
      w: 9.0,
      fontSize: 14,
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN',
      align: 'center',
      italic: true
    });
  }
}

/**
 * Generate quote slide
 */
export function generateQuoteSlide(pres, page, theme) {
  const slide = pres.addSlide();

  slide.background = { color: 'F0F8FF' };

  // Quote text
  const text = page.text || '';
  slide.addText(`"${text}"`, {
    x: 1.0,
    y: '35%',
    w: 8.0,
    fontSize: 28,
    color: theme.primary,
    align: 'center',
    fontFace: theme.fonts.body,
    lang: 'zh-CN',
    italic: true
  });

  // Author (if provided)
  const author = page.author || '';
  if (author) {
    slide.addText(`— ${author}`, {
      x: 1.0,
      y: '55%',
      w: 8.0,
      fontSize: 18,
      color: theme.text,
      align: 'right',
      fontFace: theme.fonts.body,
      lang: 'zh-CN'
    });
  }
}

/**
 * Generate summary slide
 */
export function generateSummarySlide(pres, page, theme) {
  const slide = pres.addSlide();

  // Title
  slide.addText(page.title || '总结', {
    x: 0.5,
    y: 0.5,
    w: 9.0,
    h: 0.75,
    fontSize: 36,
    bold: true,
    color: theme.primary,
    fontFace: theme.fonts.title,
    lang: 'zh-CN'
  });

  // Separator line
  slide.addShape(pres.ShapeType.rect, {
    x: 0.5,
    y: 1.3,
    w: 9.0,
    h: 0.05,
    fill: { color: theme.secondary }
  });

  // Takeaways
  const takeaways = page.takeaways || [];
  if (takeaways.length > 0) {
    slide.addText(takeaways.join('\n'), {
      x: 1.0,
      y: 1.8,
      w: 8.5,
      fontSize: 20,
      bullet: { type: 'number' },
      color: theme.text,
      fontFace: theme.fonts.body,
      lang: 'zh-CN',
      lineSpacing: 32
    });
  }
}

/**
 * Generate animation/interactive slide (placeholder)
 */
export function generateAnimationSlide(pres, page, theme) {
  const slide = pres.addSlide();

  // Title
  slide.addText(page.title || '', {
    x: 0.5,
    y: 0.5,
    w: 9.0,
    h: 0.75,
    fontSize: 28,
    bold: true,
    color: theme.primary,
    fontFace: theme.fonts.title,
    lang: 'zh-CN'
  });

  // Placeholder for animation
  const template = page.template || 'unknown';
  slide.addText(`[互动动画: ${template}]`, {
    x: 2.0,
    y: 2.5,
    w: 6.0,
    h: 2.0,
    fontSize: 24,
    color: theme.text,
    align: 'center',
    valign: 'middle',
    fontFace: theme.fonts.body,
    lang: 'zh-CN',
    fill: theme.lightBg
  });

  slide.addText('注：动画内容需在PowerPoint中手动添加', {
    x: 0.5,
    y: 5.5,
    w: 9.0,
    fontSize: 12,
    color: theme.text,
    align: 'center',
    fontFace: theme.fonts.body,
    lang: 'zh-CN',
    italic: true
  });
}

/**
 * Main generator dispatcher
 */
export const SLIDE_GENERATORS = {
  'cover': generateCoverSlide,
  'agenda': generateAgendaSlide,
  'content': generateContentSlide,
  'code': generateCodeSlide,
  'formula': generateFormulaSlide,
  'example': generateExampleSlide,
  'two_column': generateTwoColumnSlide,
  'image': generateImageSlide,
  'quote': generateQuoteSlide,
  'summary': generateSummarySlide,
  'animation': generateAnimationSlide
};

export function generateSlide(pres, page, theme) {
  const pageType = page.type || 'content';
  const generator = SLIDE_GENERATORS[pageType] || generateContentSlide;
  generator(pres, page, theme);
}
