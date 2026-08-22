import { Component, type ErrorInfo, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from './ui/Button';

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Optional custom fallback; receives the reset callback. */
  fallback?: (props: { error: Error; reset: () => void }) => ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/** Default fallback UI (functional, so it can use i18n). */
function DefaultFallback({ reset }: { reset: () => void }): JSX.Element {
  const { t } = useTranslation();
  return (
    <div className="center-screen">
      <div className="status-page">
        <div className="status-page__code">!</div>
        <h1 className="status-page__title">{t('errors.boundaryTitle')}</h1>
        <p className="status-page__body">{t('errors.boundaryBody')}</p>
        <Button variant="primary" onClick={reset}>
          {t('common.retry')}
        </Button>
      </div>
    </div>
  );
}

/** Catches render-time errors in the subtree and shows a recoverable fallback. */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Surface for local debugging; a real app would forward to telemetry.
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary caught an error', error, info);
  }

  reset = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    const { error } = this.state;
    if (error) {
      if (this.props.fallback) {
        return this.props.fallback({ error, reset: this.reset });
      }
      return <DefaultFallback reset={this.reset} />;
    }
    return this.props.children;
  }
}
