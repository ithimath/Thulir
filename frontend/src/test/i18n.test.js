import { describe, it, expect } from 'vitest';
import i18n from '../i18n/config';

describe('i18n Configuration', () => {
  it('loads English strings correctly', async () => {
    await i18n.changeLanguage('en');
    expect(i18n.t('app.name')).toBe('THULIR');
    expect(i18n.t('app.subtitle')).toBe('Early-Warning & Support System');
    expect(i18n.t('priority.critical')).toBe('Critical');
  });

  it('switches to Tamil and retrieves Tamil strings correctly', async () => {
    await i18n.changeLanguage('ta');
    expect(i18n.t('app.name')).toBe('துளிர்');
    expect(i18n.t('app.subtitle')).toBe('மாணவர் ஆரம்ப எச்சரிக்கை மற்றும் ஆதரவு தளம்');
    expect(i18n.t('priority.critical')).toBe('மிக முக்கியம்');
  });

  it('has consistent rule keys between en and ta dictionaries', () => {
    const enRules = i18n.getResourceBundle('en', 'translation').rules;
    const taRules = i18n.getResourceBundle('ta', 'translation').rules;
    expect(Object.keys(enRules)).toEqual(Object.keys(taRules));
    expect(Object.keys(enRules)).toContain('ATT_LOW');
    expect(Object.keys(enRules)).toContain('ATT_DECLINE');
    expect(Object.keys(enRules)).toContain('ATT_CONSEC');
    expect(Object.keys(enRules)).toContain('MARK_LOW');
    expect(Object.keys(enRules)).toContain('MARK_DECLINE');
  });
});

