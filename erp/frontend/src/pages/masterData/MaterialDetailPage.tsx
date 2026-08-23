import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Alert, Card, Spinner, StatusBadge } from '@/components/ui';
import { BoolCell } from '@/components/CollectionView';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { AttachmentPanel } from '@/components/AttachmentPanel';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { useRecord } from '@/hooks/useRecord';
import { formatDateTime } from '@/i18n/dates';
import { isApiError } from '@/api/types';
import { apiClient } from '@/api/client';
import type { Material } from '@/api/masterData';
import type {
  TraceabilityUnit,
  StockBalance,
  Paginated,
} from '@/api/inventory';
import type { CostLayer } from '@/api/costing';

const ENTITY_TYPE = 'catalog.Material';

export function MaterialDetailPage(): JSX.Element {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const { hasPermission } = useAuth();
  const { data, loading, error } = useRecord<Material>(
    id ? `/catalog/materials/${id}/` : null,
  );

  // --- Operational panels state ---
  const [balances, setBalances] = useState<StockBalance[]>([]);
  const [balancesLoading, setBalancesLoading] = useState(false);
  const [costLayers, setCostLayers] = useState<CostLayer[]>([]);
  const [costLayersLoading, setCostLayersLoading] = useState(false);
  const [units, setUnits] = useState<TraceabilityUnit[]>([]);
  const [unitsLoading, setUnitsLoading] = useState(false);
  const [panelsError, setPanelsError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    const load = async () => {
      setPanelsError(null);
      setBalancesLoading(true);
      setCostLayersLoading(true);
      setUnitsLoading(true);
      try {
        const [balResp, clResp, tuResp] = await Promise.all([
          apiClient.get<StockBalance[]>(
            `/inventory/movements/balances/?material=${encodeURIComponent(id)}`,
          ),
          apiClient.get<Paginated<CostLayer>>(
            `/costing/cost-layers/?material=${encodeURIComponent(id)}&page_size=50`,
          ),
          apiClient.get<Paginated<TraceabilityUnit>>(
            `/inventory/traceability-units/?material=${encodeURIComponent(id)}&page_size=100`,
          ),
        ]);
        if (!cancelled) {
          setBalances(balResp);
          setCostLayers(clResp.results);
          setUnits(tuResp.results);
        }
      } catch (err) {
        if (!cancelled) setPanelsError(isApiError(err) ? err.message : t('common.error'));
      } finally {
        if (!cancelled) {
          setBalancesLoading(false);
          setCostLayersLoading(false);
          setUnitsLoading(false);
        }
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [id, t]);

  const dash = (value: string | number | null): string =>
    value == null || value === '' ? '—' : String(value);

  const fields: DetailField[] = data
    ? [
        { labelKey: 'masterData.fields.code', value: data.code },
        { labelKey: 'masterData.fields.nameFa', value: dash(data.name_fa) },
        { labelKey: 'masterData.fields.nameEn', value: dash(data.name_en) },
        {
          labelKey: 'materials.subtype',
          value: t(`materials.subtypes.${data.subtype}`, { defaultValue: data.subtype }),
        },
        { labelKey: 'masterData.fields.baseUom', value: data.base_uom },
        { labelKey: 'materials.hazardous', value: <BoolCell value={data.is_hazardous} /> },
        { labelKey: 'materials.msdsRef', value: dash(data.msds_ref) },
        { labelKey: 'materials.leadTimeDays', value: dash(data.lead_time_days) },
        { labelKey: 'materials.shelfLifeDays', value: dash(data.shelf_life_days) },
        { labelKey: 'materials.reorderPoint', value: dash(data.reorder_point) },
        { labelKey: 'materials.safetyStock', value: dash(data.safety_stock) },
        { labelKey: 'materials.minStock', value: dash(data.min_stock) },
        { labelKey: 'materials.maxStock', value: dash(data.max_stock) },
        { labelKey: 'materials.createdAt', value: formatDateTime(data.created_at, i18n.language) },
        { labelKey: 'masterData.fields.active', value: <BoolCell value={data.is_active} /> },
      ]
    : [];

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">
          {data ? data.name_fa || data.name_en || data.code : t('materials.detail.title')}
        </h1>
        <p className="page-header__subtitle">
          <Link to="/master-data/materials" className="link-back">
            {t('materials.detail.back')}
          </Link>
        </p>
      </div>

      {loading && <Spinner />}

      {error && (
        <Alert variant="danger" title={t('common.error')}>
          {error.message}
        </Alert>
      )}

      {data && (
        <>
          <RecordDetail title={t('materials.detail.title')} fields={fields} />

          {/* ── Stock balances ── */}
          <Card>
            <h3>{t('materials.balances.title')}</h3>
            {panelsError && (
              <Alert variant="danger" title={t('common.error')}>
                {panelsError}
              </Alert>
            )}
            {balancesLoading ? (
              <Spinner />
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{t('materials.balances.warehouse')}</th>
                      <th>{t('materials.balances.unit')}</th>
                      <th className="text-end">{t('materials.balances.onHand')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {balances.length === 0 ? (
                      <tr>
                        <td colSpan={3}>{t('masterData.empty')}</td>
                      </tr>
                    ) : (
                      balances.map((b, i) => (
                        <tr key={`${b.warehouse}-${b.traceability_unit ?? 'bulk'}-${i}`}>
                          <td>{b.warehouse}</td>
                          <td>{b.traceability_unit ?? '—'}</td>
                          <td className="text-end">{b.on_hand}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* ── Cost layers ── */}
          <Card>
            <h3>{t('materials.costLayers.title')}</h3>
            {costLayersLoading ? (
              <Spinner />
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{t('materials.costLayers.date')}</th>
                      <th>{t('materials.costLayers.type')}</th>
                      <th className="text-end">{t('materials.costLayers.quantity')}</th>
                      <th className="text-end">{t('materials.costLayers.unitCost')}</th>
                      <th className="text-end">{t('materials.costLayers.totalCost')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {costLayers.length === 0 ? (
                      <tr>
                        <td colSpan={5}>{t('masterData.empty')}</td>
                      </tr>
                    ) : (
                      costLayers.map((cl) => (
                        <tr key={cl.id}>
                          <td>{cl.date}</td>
                          <td>
                            <StatusBadge status={cl.layer_type} />
                          </td>
                          <td className="text-end">{cl.quantity}</td>
                          <td className="text-end">{cl.unit_cost}</td>
                          <td className="text-end">{cl.total_cost}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* ── Traceability units ── */}
          <Card>
            <h3>{t('materials.units.title')}</h3>
            {unitsLoading ? (
              <Spinner />
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{t('materials.units.identifier')}</th>
                      <th>{t('materials.units.unitType')}</th>
                      <th className="text-end">{t('materials.units.quantity')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {units.length === 0 ? (
                      <tr>
                        <td colSpan={3}>{t('masterData.empty')}</td>
                      </tr>
                    ) : (
                      units.map((u) => (
                        <tr key={u.id}>
                          <td>{u.identifier}</td>
                          <td>
                            <StatusBadge status={u.unit_type} />
                          </td>
                          <td className="text-end">{u.quantity ?? '—'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {hasPermission('documents.attachment.view') && id && (
            <AttachmentPanel entityType={ENTITY_TYPE} entityId={id} />
          )}
          <AuditHistoryPanel entityType={ENTITY_TYPE} entityId={id ?? ''} />
        </>
      )}

      {!loading && !error && !data && (
        <Card>
          <div className="stat-card__note">{t('materials.detail.notFound')}</div>
        </Card>
      )}
    </div>
  );
}