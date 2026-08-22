import { describe, it, expect, beforeEach } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import { useTranslation } from 'react-i18next';
import i18n from '@/i18n';
import { useDirection } from '@/i18n/useDirection';

function Probe(): JSX.Element {
  useDirection();
  const { t } = useTranslation();
  return (
    <div>
      <span data-testid="title">{t('app.title')}</span>
      <span data-testid="login-submit">{t('login.submit')}</span>
    </div>
  );
}

describe('localization', () => {
  beforeEach(async () => {
    await act(async () => {
      await i18n.changeLanguage('en');
    });
  });

  it('renders English strings and sets dir=ltr for en', async () => {
    render(<Probe />);

    expect(screen.getByTestId('title')).toHaveTextContent('SLZ ERP');
    expect(screen.getByTestId('login-submit')).toHaveTextContent('Sign in');

    await waitFor(() => {
      expect(document.documentElement.getAttribute('dir')).toBe('ltr');
      expect(document.documentElement.getAttribute('lang')).toBe('en');
    });
  });

  it('switches to Persian and sets dir=rtl', async () => {
    render(<Probe />);

    await act(async () => {
      await i18n.changeLanguage('fa');
    });

    await waitFor(() => {
      expect(document.documentElement.getAttribute('dir')).toBe('rtl');
      expect(document.documentElement.getAttribute('lang')).toBe('fa');
    });

    // Persian bundle is applied (submit label differs from English).
    expect(screen.getByTestId('login-submit')).not.toHaveTextContent('Sign in');
  });
});
