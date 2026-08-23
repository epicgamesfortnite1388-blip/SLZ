import { useState, type ReactNode } from 'react';
import { Button, type ButtonProps } from './Button';

export interface ConfirmButtonProps extends Omit<ButtonProps, 'onClick'> {
  /** Message shown before the action fires. */
  confirmMessage: string;
  onConfirm: () => void;
  children: ReactNode;
}

/**
 * Two-step destructive-action button: first click arms it ("confirm?"),
 * second click fires. Arms state resets on blur or after firing. Prevents
 * accidental cancels/reversals without a heavyweight modal.
 */
export function ConfirmButton({
  confirmMessage,
  onConfirm,
  children,
  disabled,
  ...rest
}: ConfirmButtonProps): JSX.Element {
  const [armed, setArmed] = useState(false);

  if (!armed) {
    return (
      <Button {...rest} disabled={disabled} onClick={() => setArmed(true)}>
        {children}
      </Button>
    );
  }

  return (
    <Button
      {...rest}
      variant="danger"
      disabled={disabled}
      onBlur={() => setArmed(false)}
      onClick={() => {
        setArmed(false);
        onConfirm();
      }}
    >
      {confirmMessage}
    </Button>
  );
}
