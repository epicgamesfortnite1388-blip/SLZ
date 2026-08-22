import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import {
  fetchQualityPlan,
  listQualityPlanItems,
  listQualityPlanRevisions,
  type QualityPlanItem,
  type QualityPlanRevision,
} from '@/api/quality';
import { isApiError } from '@/api/types';
import { AttachmentPanel } from '@/components/AttachmentPanel';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { BoolCell } from '@/components/CollectionView';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { Alert, Button, Card, Spinner } from '@/components/ui';
import { useAuth } from '@/auth/AuthContext';

const when = (iso: string | null): string => (iso ? iso.replace('T', ' ').slice(0, 10) : '—');

/**
 * Read-only detail of one quality-plan root: binding header, the full revision
 * chain (draft → active → superseded), and the selected revision's inspection
 * items. Execution/sampling enforcement is gated (Q-039/040); this page only
 * presents the confirmed plan definition.
 */
export function QualityPlanRootDetailPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const { id: rootId = '' } = useParams();
  const [plan, setPlan] = useState<Awaited<ReturnType<typeof fetchQualityPlan>> | null>(null);
  const [revisions, setRevisions] = useState<QualityPlanRevision[] | null>(null);
  const [selected, setSelected] = useState<QualityPlanRevision | null>(null);
  const [items, setItems] = useState<QualityPlanItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setError(null);
    Promise.all([fetchQualityPlan(rootId), listQualityPlanRevisions(rootId)])
      .then(([root, revs]) => {
        if (!active) return;
        setPlan(root);
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

  useEffect(() => {
    if (!selected) return;
    let active = true;
    setItems(null);
    listQualityPlanItems(selected.id)
      .then((rows) => {
        if (active) setItems(rows);
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

  if (!plan || !revisions) {
    return (
      <div className="table-state">
        <Spinner label={t('common.loading')} />
      </div>
    );
  }

  const headerFields: DetailField[] = [
    { labelKey: 'quality.fields.specRevision', value: plan.spec_revision },
    { labelKey: 'masterData.fields.active', value: <BoolCell value={plan.is_active} /> },
  ];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('quality.detail.planTitle')}</h1>
        <p className="page-header__subtitle">{t('quality.detail.planSubtitle')}</p>
      </div>

      <RecordDetail title={t('quality.detail.headerTitle')} fields={headerFields} />

      <Card title={t('quality.detail.revisionsTitle')}>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('quality.fields.revisionNumber')}</th>
                <th>{t('engineering.fields.status')}</th>
                <th>{t('quality.fields.effectiveFrom')}</th>
                <th>{t('engineering.fields.effectiveTo')}</th>
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
                  <td>{t(`engineering.statuses.${rev.status}`)}</td>
                  <td>{when(rev.effective_from)}</td>
                  <td>{when(rev.effective_to)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {selected && (
        <Card title={`${t('quality.detail.itemsTitle')} — #${selected.revision_number}`}>
          {!items && (
            <div className="table-state">
              <Spinner label={t('common.loading')} />
            </div>
          )}
          {items && items.length === 0 && <p>{t('masterData.empty')}</p>}
          {items && items.length > 0 && (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>{t('quality.detail.characteristic')}</th>
                    <th>{t('quality.detail.workCenter')}</th>
                    <th>{t('quality.detail.stageLabel')}</th>
                    <th>{t('quality.detail.target')}</th>
                    <th>{t('quality.detail.limits')}</th>
                    <th>{t('quality.detail.sampling')}</th>
                    <th>{t('quality.detail.mandatory')}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>{item.sequence}</td>
                      <td>{item.characteristic}</td>
                      <td>{item.work_center || '—'}</td>
                      <td>{item.stage_label || '—'}</td>
                      <td>
                        {item.target == null
                          ? '—'
                          : `${item.target}${item.unit ? ` ${item.unit}` : ''}`}
                      </td>
                      <td>
                        {item.lower_limit == null && item.upper_limit == null
                          ? '—'
                          : `${item.lower_limit ?? ''} … ${item.upper_limit ?? ''}`}
                      </td>
                      {/* Free text — sampling policy is OPEN (Q-039/040). */}
                      <td>{item.sampling || '—'}</td>
                      <td>
                        <BoolCell value={item.is_mandatory} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p>
            <Link to="/quality/plans" className="link-back">
              ← {t('common.back')}
            </Link>
          </p>
        </Card>
      )}

      <AuditHistoryPanel entityType="quality.QualityPlan" entityId={plan.id} />

      {hasPermission('documents.attachment.view') && (
        <AttachmentPanel entityType="quality.QualityPlan" entityId={plan.id} />
      )}

      <div className="form-actions">
        <Link to="/quality/plans" className="link-back">
          ← {t('common.back')}
        </Link>
      </div>
    </div>
  );
}
