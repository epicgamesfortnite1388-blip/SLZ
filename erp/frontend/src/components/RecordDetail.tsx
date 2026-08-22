import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Card } from '@/components/ui';

/** One row in a record-detail view: a translated label and its value. */
export interface DetailField {
  labelKey: string;
  value: ReactNode;
}

interface RecordDetailProps {
  /** Optional card title (already translated by the caller). */
  title?: string;
  fields: DetailField[];
}

/**
 * Read-only label/value presentation of a single record. Purely presentational
 * and generic — the caller maps a typed record to {@link DetailField} rows, so
 * this component encodes no per-entity knowledge and can back any detail screen.
 */
export function RecordDetail({ title, fields }: RecordDetailProps): JSX.Element {
  const { t } = useTranslation();
  return (
    <Card title={title}>
      <dl className="detail-grid">
        {fields.map((field) => (
          <div className="detail-grid__row" key={field.labelKey}>
            <dt className="detail-grid__label">{t(field.labelKey)}</dt>
            <dd className="detail-grid__value">{field.value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}
