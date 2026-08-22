import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Alert, Button, Card, Spinner } from '@/components/ui';
import type { UseCollectionResult } from '@/hooks/useCollection';

export interface Column<T> {
  /** i18n key for the header label. */
  headerKey: string;
  /** Cell renderer. */
  render: (row: T) => ReactNode;
  /** Optional cell alignment. */
  align?: 'start' | 'end' | 'center';
}

export interface CollectionViewProps<T> {
  titleKey: string;
  subtitleKey?: string;
  columns: Column<T>[];
  /** Row identity for React keys. */
  rowKey: (row: T) => string;
  collection: UseCollectionResult<T>;
  /** Optional header-area action (e.g. a permission-gated "New" button). */
  headerAction?: ReactNode;
  /** Optional row activation (e.g. open a detail view). Rows become clickable. */
  onRowClick?: (row: T) => void;
}

/**
 * Generic master-data browse view. Handles loading / error / empty / data
 * states, search, and pagination consistently across every master-data screen.
 * Direction (RTL/LTR) is inherited from the document via CSS logical props.
 */
export function CollectionView<T>({
  titleKey,
  subtitleKey,
  columns,
  rowKey,
  collection,
  headerAction,
  onRowClick,
}: CollectionViewProps<T>): JSX.Element {
  const { t } = useTranslation();
  const { data, loading, error, page, search, setPage, setSearch, reload } =
    collection;

  const rows = data?.results ?? [];
  const totalPages = data?.total_pages ?? 1;

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t(titleKey)}</h1>
        {subtitleKey && (
          <p className="page-header__subtitle">{t(subtitleKey)}</p>
        )}
      </div>

      <Card>
        <div className="table-toolbar">
          <input
            type="search"
            className="input"
            value={search}
            placeholder={t('masterData.searchPlaceholder')}
            onChange={(e) => setSearch(e.target.value)}
            aria-label={t('masterData.searchPlaceholder')}
          />
          {headerAction && <div className="table-toolbar__actions">{headerAction}</div>}
        </div>

        {loading && (
          <div className="table-state">
            <Spinner label={t('common.loading')} />
          </div>
        )}

        {!loading && error && (
          <Alert variant="danger" title={t('common.error')}>
            <p>{error.message}</p>
            <Button variant="secondary" size="sm" onClick={reload}>
              {t('common.retry')}
            </Button>
          </Alert>
        )}

        {!loading && !error && rows.length === 0 && (
          <div className="table-state table-state--empty">
            {t('masterData.empty')}
          </div>
        )}

        {!loading && !error && rows.length > 0 && (
          <>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    {columns.map((col) => (
                      <th
                        key={col.headerKey}
                        className={col.align ? `text-${col.align}` : undefined}
                      >
                        {t(col.headerKey)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr
                      key={rowKey(row)}
                      onClick={onRowClick ? () => onRowClick(row) : undefined}
                      className={onRowClick ? 'data-table__row--clickable' : undefined}
                    >
                      {columns.map((col) => (
                        <td
                          key={col.headerKey}
                          className={col.align ? `text-${col.align}` : undefined}
                        >
                          {col.render(row)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                {t('masterData.prev')}
              </Button>
              <span className="pagination__status">
                {t('masterData.pageOf', { page, total: totalPages })}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                {t('masterData.next')}
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

/** Shared yes/no cell for boolean flags. */
export function BoolCell({ value }: { value: boolean }): JSX.Element {
  const { t } = useTranslation();
  return <span>{value ? t('common.yes') : t('common.no')}</span>;
}
