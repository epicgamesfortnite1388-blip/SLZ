import type { HTMLAttributes, ReactNode } from 'react';

export interface CardProps extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  /** Optional card heading rendered above the content. */
  title?: ReactNode;
  /** Optional element rendered on the trailing edge of the header. */
  actions?: ReactNode;
  padded?: boolean;
}

/** Surface container primitive. */
export function Card({
  title,
  actions,
  padded = true,
  className,
  children,
  ...rest
}: CardProps): JSX.Element {
  const classes = ['card', padded ? 'card--padded' : '', className ?? '']
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes} {...rest}>
      {(title || actions) && (
        <div className="card__header">
          {title && <div className="card__title">{title}</div>}
          {actions && <div className="card__actions">{actions}</div>}
        </div>
      )}
      <div className="card__body">{children}</div>
    </div>
  );
}
