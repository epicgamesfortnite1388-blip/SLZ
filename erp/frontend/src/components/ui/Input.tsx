import { forwardRef, type InputHTMLAttributes } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

/** Text input primitive. */
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { invalid = false, className, ...rest },
  ref,
) {
  const classes = ['input', invalid ? 'input--invalid' : '', className ?? '']
    .filter(Boolean)
    .join(' ');

  return (
    <input
      ref={ref}
      className={classes}
      aria-invalid={invalid || undefined}
      {...rest}
    />
  );
});
