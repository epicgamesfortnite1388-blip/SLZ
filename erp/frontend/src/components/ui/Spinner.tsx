export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  /** Render inline (e.g. inside a button) rather than as a block. */
  inline?: boolean;
  label?: string;
}

/** Indeterminate loading indicator. */
export function Spinner({
  size = 'md',
  inline = false,
  label,
}: SpinnerProps): JSX.Element {
  const classes = ['spinner', `spinner--${size}`, inline ? 'spinner--inline' : '']
    .filter(Boolean)
    .join(' ');

  return (
    <span className={classes} role="status" aria-live="polite">
      <span className="spinner__ring" aria-hidden="true" />
      {label ? (
        <span className="spinner__label">{label}</span>
      ) : (
        <span className="visually-hidden">Loading</span>
      )}
    </span>
  );
}
