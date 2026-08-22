import type { ReactNode } from 'react';

export type AlertVariant = 'info' | 'success' | 'warning' | 'danger';

export interface AlertProps {
  variant?: AlertVariant;
  title?: ReactNode;
  children?: ReactNode;
  /** Optional dismiss handler; renders a close button when provided. */
  onClose?: () => void;
  closeLabel?: string;
}

/** Inline status / feedback message. */
export function Alert({
  variant = 'info',
  title,
  children,
  onClose,
  closeLabel = 'Close',
}: AlertProps): JSX.Element {
  return (
    <div className={`alert alert--${variant}`} role="alert">
      <div className="alert__content">
        {title && <div className="alert__title">{title}</div>}
        {children && <div className="alert__body">{children}</div>}
      </div>
      {onClose && (
        <button
          type="button"
          className="alert__close"
          onClick={onClose}
          aria-label={closeLabel}
        >
          ×
        </button>
      )}
    </div>
  );
}
