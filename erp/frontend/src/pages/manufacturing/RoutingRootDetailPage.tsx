import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import {
  fetchRouting,
  listRoutingOperations,
  listRoutingRevisions,
  type RoutingOperation,
  type StructureRevision,
} from '@/api/manufacturing';
import { isApiError } from '@/api/types';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { BoolCell } from '@/components/CollectionView';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { Alert, Button, Card, Spinner } from '@/components/ui';

const when = (iso: string | null): string => (iso ? iso.replace('T', ' ').slice(0, 10) : '—');

/**
 * Read-only detail of one routing root: identity header, the full revision
 * chain, and the selected revision's ordered operations. Operation editing
 * stays on the DRAFT workflow; this page never mutates anything.
 */
export function RoutingRootDetailPage(): JSX.Element {
  const { t } = useTranslation();
  const { rootId = '' } = useParams();
  const [routing, setRouting] = useState<Awaited<ReturnType<typeof fetchRouting>> | null>(null);
  const [revisions, setRevisions] = useState<StructureRevision[] | null>(null);
  const [selected, setSelected] = useState<StructureRevision | null>(null);
  const [operations, setOperations] = useState<RoutingOperation[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load the root record + its whole revision chain once.
  useEffect(() => {
    let active = true;
    setError(null);
    Promise.all([fetchRouting(rootId), listRoutingRevisions(rootId)])
      .then(([root, revs]) => {
        if (!active) return;
        setRouting(root);
        setRevisions(revs);
        setSelected(revs.find((r) => r.status === 'ACTIVE') ?? revs[0] ?? null);
      })
      .catch((err: unknown) => {
        if (active) setError(isApiError(err) ? err.message : t('common.error'));
      });
    return () => {
      active = false;
    };
  }, [rootId, t]);

  // Load the selected revision's operations.
  useEffect(() => {
    if (!selected) return;
    let active = true;
    setOperations(null);
    listRoutingOperations(selected.id)
      .then((ops) => {
        if (active) setOperations(ops);
      })
      .catch((err: unknown) => {
        if (active) setError(isApiError(err) ? err.message : t('common.error'));
      });
    return () => {
      active = false;
    };
  }, [selected, t]);

  if (error) {
    return (
      <div className="stack">
        <Alert variant="danger" title={t('common.error')}>
          <p>{error}</p>
          <Button variant="secondary" size="sm" onClick={() => window.history.back()}>
            {t('common.back')}
          </Button>
        </Alert>
      </div>
    );
  }

  if (!routing || !revisions) {
    return (
      <div className="table-state">
        <Spinner label={t('common.loading')} />
      </div>
    );
  }

  const headerFields: DetailField[] = [
    { labelKey: 'manufacturing.fields.specRevision', value: routing.spec_revision },
    { labelKey: 'masterData.fields.active', value: <BoolCell value={routing.is_active} /> },
  ];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('manufacturing.detail.routingTitle')}</h1>
        <p className="page-header__subtitle">{t('manufacturing.detail.routingSubtitle')}</p>
      </div>

      <RecordDetail title={t('manufacturing.detail.headerTitle')} fields={headerFields} />

      <Card title={t('manufacturing.detail.revisionsTitle')}>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('manufacturing.fields.revisionNumber')}</th>
                <th>{t('engineering.fields.status')}</th>
                <th>{t('manufacturing.fields.effectiveFrom')}</th>
                <th>{t('engineering.fields.effectiveTo')}</th>
                <th>{t('engineering.fields.changeReason')}</th>
              </tr>
            </thead>
            <tbody>
              {revisions.map((rev) => (
                <tr
                  key={rev.id}
                  onClick={() => setSelected(rev)}
                  className={
                    selected?.id === rev.id ? 'data-table__row--clickable' : undefined
                  }
                  style={selected?.id === rev.id ? { fontWeight: 600 } : undefined}
                >
                  <td>#{rev.revision_number}</td>
                  <td>{t(`manufacturing.statuses.${rev.status}`)}</td>
                  <td>{when(rev.effective_from)}</td>
                  <td>{when(rev.effective_to)}</td>
                  <td>{rev.change_reason || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {selected && (
        <Card
          title={`${t('manufacturing.detail.operationsTitle')} — #${selected.revision_number}`}
        >
          {!operations && (
            <div className="table-state">
              <Spinner label={t('common.loading')} />
            </div>
          )}
          {operations && operations.length === 0 && <p>{t('masterData.empty')}</p>}
          {operations && operations.length > 0 && (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>{t('manufacturing.fields.opWorkCenter')}</th>
                    <th>{t('manufacturing.fields.opName')}</th>
                    <th>{t('manufacturing.fields.outputMaterial')}</th>
                    <th>{t('manufacturing.fields.setupTime')}</th>
                    <th>{t('manufacturing.fields.runRate')}</th>
                    <th>{t('sales.fields.notes')}</th>
                  </tr>
                </thead>
                <tbody>
                  {operations.map((op) => (
                    <tr key={op.id}>
                      <td>{op.sequence}</td>
                      <td>{op.work_center}</td>
                      <td>{op.operation_name}</td>
                      <td>{op.output_material ?? '—'}</td>
                      <td>{op.setup_time_minutes ?? '—'}</td>
                      {/* run_rate + basis are informational; standard templates are OPEN (Q-029). */}
                      <td>
                        {op.run_rate === null
                          ? '—'
                          : `${op.run_rate}${op.run_rate_basis ? ` / ${op.run_rate_basis}` : ''}`}
                      </td>
                      <td>{op.notes || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p>
            <Link to="/manufacturing/routing-revisions" className="link-back">
              {t('manufacturing.routings.title')} →
            </Link>
          </p>
        </Card>
      )}

      <AuditHistoryPanel entityType="manufacturing.Routing" entityId={routing.id} />

      <div className="form-actions">
        <Link to="/manufacturing/routings" className="link-back">
          ← {t('common.back')}
        </Link>
      </div>
    </div>
  );
}
