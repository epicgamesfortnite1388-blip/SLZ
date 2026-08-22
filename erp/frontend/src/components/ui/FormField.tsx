import { useId, type ReactNode } from 'react';

export interface FormFieldProps {
  label: ReactNode;
  /** Field control. Receives the generated id via a render prop. */
  children: (field: { id: string; describedBy?: string }) => ReactNode;
  error?: ReactNode;
  hint?: ReactNode;
  required?: boolean;
}

/**
 * Accessible label + control + error/hint wrapper.
 * Wires up `htmlFor`, `aria-describedby`, and required indicators.
 */
export function FormField({
  label,
  children,
  error,
  hint,
  required = false,
}: FormFieldProps): JSX.Element {
  const id = useId();
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy =
    [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(' ') ||
    undefined;

  return (
    <div className="form-field">
      <label className="form-field__label" htmlFor={id}>
        {label}
        {required && (
          <span className="form-field__required" aria-hidden="true">
            {' '}
            *
          </span>
        )}
      </label>
      {children({ id, describedBy })}
      {hint && !error && (
        <p className="form-field__hint" id={hintId}>
          {hint}
        </p>
      )}
      {error && (
        <p className="form-field__error" id={errorId}>
          {error}
        </p>
      )}
    </div>
  );
}
