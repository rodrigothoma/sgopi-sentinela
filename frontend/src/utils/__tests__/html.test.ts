import { describe, expect, it } from 'vitest';
import { escaparHtml } from '../html';

describe('escaparHtml (XSS armazenado no popup Leaflet)', () => {
  it('neutraliza markup vindo da natureza livre do registro público', () => {
    const natureza = '<img src=x onerror="alert(document.cookie)">';
    expect(escaparHtml(natureza)).toBe('&lt;img src=x onerror=&quot;alert(document.cookie)&quot;&gt;');
  });

  it('escapa aspas simples e e-comercial e aceita valores não-string', () => {
    expect(escaparHtml("a & 'b'")).toBe('a &amp; &#39;b&#39;');
    expect(escaparHtml(42)).toBe('42');
    expect(escaparHtml(null)).toBe('');
    expect(escaparHtml(undefined)).toBe('');
  });
});
