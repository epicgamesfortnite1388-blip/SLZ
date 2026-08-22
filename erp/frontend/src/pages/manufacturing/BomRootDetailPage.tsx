import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import {
  fetchBom,
  listBomLines,
  listBomRevisions,
  type BomLine,
  type StructureRevision,
} from '@/api/manufacturing';
import { isApiError } from '@/api/types';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { BoolCell } from '@/components/CollectionView';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { Alert, Button, Card, Spinner } from '@/components/ui';

const when = (iso: string | null): string => (iso ? iso.replace('T', ' ').slice(0, 10) : '—');

/**
 * Read-only detail of one BOM root: identity header, the full revision chain
 * (draft → active → superseded), and the selected revision's material lines.
 * Line editing stays on the DRAFT workflow; this page never mutates anything.
 */
export function BomRootDetailPage(): JSX.Element {
  const { t } = useTranslation();
  const { id: rootId = '' } = useParams();
  const [bom, setBom] = useState<Awaited<ReturnType<typeof fetchBom>> | null>(null);
  const [revisions, setRevisions] = useState<StructureRevision[] | null>(null);
  const [selected, setSelected] = useState<StructureRevision | null>(null);
  const [lines, setLines] = useState<BomLine[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load the root record + its whole revision chain once.
  useEffect(() => {
    let active = true;
    setError(null);
    Promise.all([fetchBom(rootId), listBomRevisions(rootId)])
      .then(([root, revs]) => {
        if (!active) return;
        setBom(root);
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

  // Load the selected revision's material lines.
  useEffect(() => {
    if (!selected) return;
    let active = true;
    setLines(null);
    listBomLines(selected.id)
      .then((ls) => {
        if (active) setLines(ls);
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

  if (!bom || !revisions) {
    return (
      <div className="table-state">
        <Spinner label={t('common.loading')} />
      </div>
    );
  }

  const headerFields: DetailField[] = [
    { labelKey: 'manufacturing.fields.specRevision', value: bom.spec_revision },
    {
      labelKey: 'manufacturing.fields.outputMaterial',
      value: bom.output_material ?? '—',
    },
    { labelKey: 'masterData.fields.active', value: <BoolCell value={bom.is_active} /> },
  ];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('manufacturing.detail.bomTitle')}</h1>
        <p className="page-header__subtitle">{t('manufacturing.detail.bomSubtitle')}</p>
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
        <Card title={`${t('manufacturing.detail.linesTitle')} — #${selected.revision_number}`}>
          {!lines && (
            <div className="table-state">
              <Spinner label={t('common.loading')} />
            </div>
          )}
          {lines && lines.length === 0 && <p>{t('masterData.empty')}</p>}
          {lines && lines.length > 0 && (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>{t('manufacturing.fields.lineMaterial')}</th>
                    <th>{t('manufacturing.fields.lineQuantity')}</th>
                    <th>{t('masterData.fields.uom')}</th>
                    <th>{t('manufacturing.fields.consumptionBasis')}</th>
                    <th>{t('manufacturing.fields.scrapPct')}</th>
                    <th>{t('sales.fields.notes')}</th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((line) => (
                    <tr key={line.id}>
                      <td>{line.sequence}</td>
                      <td>{line.material}</td>
                      <td>{line.quantity_per_output}</td>
                      <td>{line.uom}</td>
                      {/* Free text — the canonical basis set is OPEN (Q-027). */}
                      <td>{line.consumption_basis || '—'}</td>
                      <td>{line.scrap_pct ?? '—'}</td>
                      <td>{line.notes || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p>
            <Link to="/manufacturing/bom-revisions" className="link-back">
              {t('manufacturing.boms.title')} →
            </Link>
          </p>
        </Card>
      )}

      <AuditHistoryPanel entityType="manufacturing.BillOfMaterials" entityId={bom.id} />

      <div className="form-actions">
        <Link to="/manufacturing/boms" className="link-back">
          ← {t('common.back')}
        </Link>
      </div>
    </div>
  );
}
