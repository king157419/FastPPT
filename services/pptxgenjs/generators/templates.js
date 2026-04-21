/**
 * Theme and template configurations for teaching presentations
 */

export const THEMES = {
  education: {
    primary: '4472C4',
    secondary: 'ED7D31',
    accent: '70AD47',
    text: '404040',
    background: 'FFFFFF',
    lightBg: 'F5F5F5',
    fonts: {
      title: 'Microsoft YaHei',
      body: 'Microsoft YaHei',
      code: 'Consolas'
    }
  },
  business: {
    primary: '1F4E78',
    secondary: 'C55A11',
    accent: '548235',
    text: '333333',
    background: 'F8F9FA',
    lightBg: 'F0F0F0',
    fonts: {
      title: 'Microsoft YaHei',
      body: 'Microsoft YaHei',
      code: 'Courier New'
    }
  }
};

export const LAYOUT_CONFIG = {
  wide: {
    name: 'LAYOUT_WIDE',
    width: 10,
    height: 5.625,
    margin: { x: 0.5, y: 0.5 }
  },
  standard: {
    name: 'LAYOUT_16x9',
    width: 10,
    height: 5.625,
    margin: { x: 0.5, y: 0.5 }
  }
};

export function getTheme(themeName = 'education') {
  return THEMES[themeName] || THEMES.education;
}

export function getLayout(layoutName = 'wide') {
  return LAYOUT_CONFIG[layoutName] || LAYOUT_CONFIG.wide;
}
