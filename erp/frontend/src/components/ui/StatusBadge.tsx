import type { ReactNode } from 'react';

/** Semantic variant mapped to a design-token color palette. */
export type StatusVariant =
  | 'neutral'
  | 'info'
  | 'success'
  | 'warning'
  | 'danger'
  | 'accent';

/** Maps logical disposition/status keywords to a visual variant. */
const STATUS_VARIANT_MAP: Record<string, StatusVariant> = {
  // Generic
  DRAFT: 'neutral',
  ACTIVE: 'success',
  ARCHIVED: 'info',
  SUPERSEDED: 'warning',
  // Procurement
  SUBMITTED: 'info',
  APPROVED: 'success',
  REJECTED: 'danger',
  CANCELLED: 'danger',
  SENT: 'info',
  CLOSED: 'neutral',
  // Sales
  CONFIRMED: 'success',
  // Production
  RELEASED: 'info',
  COMPLETED: 'success',
  // QC
  PASS: 'success',
  FAIL: 'danger',
  HOLD: 'warning',
  // Allocation — RESERVED is like 'in use', distinct from shop-floor RELEASED
  RESERVED: 'accent',
  // Workflow
  UNDER_REVIEW: 'warning',
  // Inventory
  QUARANTINED: 'warning',
  // Generic pos/neg
  LOCKED: 'danger',
  EXPIRED: 'danger',
  PENDING: 'warning',
};

export interface StatusBadgeProps {
  /** The raw status value (e.g. 'DRAFT', 'CONFIRMED'). */
  status: string;
  /** Optional translated label override. Falls back to raw status. */
  label?: ReactNode;
  /** Override auto-detected variant. */
  variant?: StatusVariant;
  /** Size variant. */
  size?: 'sm' | 'md';
}

/**
 * Color-coded status badge. Auto-maps known status strings to visual variants,
 * with an explicit override for edge cases. Use across all list/detail pages
 * for consistent status visualization.
 */
export function StatusBadge({
  status,
  label,
  variant: explicitVariant,
  size = 'sm',
}: StatusBadgeProps): JSX.Element {
  const variant = explicitVariant ?? STATUS_VARIANT_MAP[status] ?? 'neutral';
  const display = label ?? status;

  const classes = [
    'status-badge',
    `status-badge--${variant}`,
    size === 'md' ? 'status-badge--md' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return <span className={classes}>{display}</span>;
}