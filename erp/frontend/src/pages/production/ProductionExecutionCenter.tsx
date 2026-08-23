import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { apiClient } from '@/api/client';
import {
  createMaterialIssue,
  createProductionOutput,
  fetchMaterialIssues,
  fetchProductionOutputs,
  transitionProductionOrder,
  type MaterialIssue,
  type MaterialIssueMethod,
  type ProductionOrder,
  type ProductionOutput,
} from '@/api/production';
import {
  createTraceabilityUnit,
  fetchTraceabilityUnits,
  type TraceabilityUnit,
  type TraceabilityUnitType,
  type Warehouse,
} from '@/api/inventory';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner, StatusBadge } from '@/components/ui';

interface Option {
  id: string;
  number?: string;
  code?: string;
  name_fa?: string;
  name_en?: string;
  company?: string;
  status?: string;
  customer_product?: string;
  planned_quantity?: string;
  uom?: string;
}

const UNIT_TYPES: TraceabilityUnitType[] = ['BATCH', 'ROLL', 'CARTON', 'PALLET'];

export function ProductionExecutionCenter(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canView = hasPermission('production.execution.view');
  const canManage = hasPermission('production.execution.manage');

  // ── Ref data ──
  const [orders, setOrders] = useState<Option[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [materials, setMaterials] = useState<Option[]>([]);
  const [uoms, setUoms] = useState<Option[]>([]);
  const [units, setUnits] = useState<TraceabilityUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ── Selected order ──
  const [selectedOrderId, setSelectedOrderId] = useState('');
  const [selectedOrder, setSelectedOrder] = useState<ProductionOrder | null>(null);
  const [issues, setIssues] = useState<MaterialIssue[]>([]);
  const [outputs, setOutputs] = useState<ProductionOutput[]>([]);
  const [execLoading, setExecLoading] = useState(false);
  const [busy, setBusy] = useState(false);

  // ── Issue form ──
  const [issueMaterial, setIssueMaterial] = useState('');
  const [issueUnit, setIssueUnit] = useState('');
  const [issueWarehouse, setIssueWarehouse] = useState('');
  const [issueQuantity, setIssueQuantity] = useState('');
  const [issueMethod, setIssueMethod] = useState<MaterialIssueMethod>('EXPLICIT');
  const [issueUom, setIssueUom] = useState('');

  // ── Output form ──
  const [outputUnit, setOutputUnit] = useState('');
  const [outputWarehouse, setOutputWarehouse] = useState('');
  const [outputQuantity, setOutputQuantity] = useState('');
  const [outputUom, setOutputUom] = useState('');

  // ── New-traceability-unit form ──
  const [unitType, setUnitType] = useState<TraceabilityUnitType>('ROLL');
  const [unitIdentifier, setUnitIdentifier] = useState('');
  const [unitMaterial, setUnitMaterial] = useState('');
  const [unitQuantity, setUnitQuantity] = useState('');

  const label = (o: Option): string => o.name_fa || o.name_en || o.code || o.number || o.id;
  const unitLabel = (u: TraceabilityUnit): string => `${u.identifier} (${u.unit_type})`;

  // ── Initial load (orders + ref data) ──
  useEffect(() => {
    if (!canView) return;
    let cancelled = false;
    const init = async () => {
      setLoading(true);
      try {
        const [ordRes, whRes, matRes, uomRes] = await Promise.all([
          apiClient.get<Paginated<Option>>('/production/orders/?status=RELEASED&page_size=100'),
          apiClient.get<Paginated<Warehouse>>('/inventory/warehouses/?page_size=100'),
          apiClient.get<Paginated<Option>>('/catalog/materials/?page_size=100'),
          apiClient.get<Paginated<Option>>('/catalog/uoms/?page_size=100'),
        ]);
        if (!cancelled) {
          setOrders(ordRes.results);
          setWarehouses(whRes.results);
          setMaterials(matRes.results);
          setUoms(uomRes.results);
        }
      } catch (err) {
        if (!cancelled) setError(isApiError(err) ? err.message : t('common.error'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void init();
    return () => { cancelled = true; };
  }, [canView, t]);

  // ── Load execution data when order changes ──
  useEffect(() => {
    if (!selectedOrderId) return;
    let cancelled = false;
    const loadExec = async () => {
      setExecLoading(true);
      setError(null);
      try {
        // Fetch order first, then use its company for scoped queries.
        const orderDetail = await apiClient.get<ProductionOrder>(
          `/production/orders/${selectedOrderId}/`,
        );
        const [unitsRes, issuesRes, outputsRes] = await Promise.all([
          fetchTraceabilityUnits(`?company=${encodeURIComponent(orderDetail.company)}&page_size=200`),
          fetchMaterialIssues(selectedOrderId),
          fetchProductionOutputs(selectedOrderId),
        ]);
        if (!cancelled) {
          setSelectedOrder(orderDetail);
          setUnits(unitsRes.results);
          setIssues(issuesRes.results);
          setOutputs(outputsRes.results);
          // set defaults
          if (!issueWarehouse && warehouses[0]) setIssueWarehouse(warehouses[0].id);
          if (!outputWarehouse && warehouses[0]) setOutputWarehouse(warehouses[0].id);
          if (!issueMaterial && materials[0]) setIssueMaterial(materials[0].id);
          if (!unitMaterial && materials[0]) setUnitMaterial(materials[0].id);
          if (!issueUom && uoms[0]) setIssueUom(uoms[0].id);
          if (!outputUom && uoms[0]) setOutputUom(uoms[0].id);
        }
      } catch (err) {
        if (!cancelled) setError(isApiError(err) ? err.message : t('common.error'));
      } finally {
        if (!cancelled) setExecLoading(false);
      }
    };
    void loadExec();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedOrderId]);

  const reloadExec = async () => {
    if (!selectedOrderId) return;
    try {
      const [orderDetail, unitsRes, issuesRes, outputsRes] = await Promise.all([
        apiClient.get<ProductionOrder>(`/production/orders/${selectedOrderId}/`),
        fetchTraceabilityUnits(`?company=${encodeURIComponent(selectedOrder?.company ?? '')}&page_size=200`),
        fetchMaterialIssues(selectedOrderId),
        fetchProductionOutputs(selectedOrderId),
      ]);
      setSelectedOrder(orderDetail);
      setUnits(unitsRes.results);
      setIssues(issuesRes.results);
      setOutputs(outputsRes.results);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    }
  };

  // ── Select helper ──
  const selectField = (
    labelKey: string,
    value: string,
    onChange: (v: string) => void,
    options: Option[] | Warehouse[] | TraceabilityUnit[],
    required = true,
  ) => (
    <FormField label={t(labelKey)} required={required}>
      {({ id }) => (
        <select
          className="input"
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={required}
          disabled={!canManage || busy}
        >
          <option value="">—</option>
          {options.map((o) => {
            const item = o as Option & Warehouse & TraceabilityUnit;
            const txt = 'identifier' in item ? unitLabel(item) : label(item);
            return <option key={item.id} value={item.id}>{txt}</option>;
          })}
        </select>
      )}
    </FormField>
  );

  // ── Post material issue ──
  const postIssue = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await createMaterialIssue({
        production_order: selectedOrderId,
        material: issueMaterial,
        traceability_unit: issueMethod === 'EXPLICIT' ? issueUnit : null,
        warehouse: issueWarehouse,
        quantity: issueQuantity,
        uom: issueUom,
        method: issueMethod,
      });
      setIssueQuantity('');
      setIssueUnit('');
      await reloadExec();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally { setBusy(false); }
  };

  // ── Post production output ──
  const postOutput = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await createProductionOutput({
        production_order: selectedOrderId,
        traceability_unit: outputUnit,
        warehouse: outputWarehouse,
        quantity: outputQuantity,
        uom: outputUom,
      });
      setOutputQuantity('');
      await reloadExec();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally { setBusy(false); }
  };

  // ── Register new traceability unit ──
  const registerUnit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const created = await createTraceabilityUnit({
        company: selectedOrder?.company,
        material: unitMaterial || null,
        customer_product_id: selectedOrder?.customer_product,
        unit_type: unitType,
        identifier: unitIdentifier,
        quantity: unitQuantity || null,
        uom: outputUom || issueUom || selectedOrder?.uom,
      });
      setOutputUnit(created.id);
      setUnitIdentifier('');
      setUnitQuantity('');
      await reloadExec();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally { setBusy(false); }
  };

  // ── Complete order action ──
  const completeOrder = async () => {
    if (!selectedOrderId) return;
    setBusy(true);
    try {
      await transitionProductionOrder(selectedOrderId, 'complete');
      await reloadExec();
      // Remove from order list
      setOrders((prev) => prev.filter((o) => o.id !== selectedOrderId));
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally { setBusy(false); }
  };

  if (!canView) return <></>;

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('production.executionCenter.title')}</h1>
        <p className="page-header__subtitle">{t('production.executionCenter.subtitle')}</p>
      </div>

      {loading && <Card><Spinner /></Card>}
      {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}

      {/* ── Order selector ── */}
      {!loading && (
        <Card>
          <FormField label={t('production.executionCenter.selectOrder')} required>
            {({ id }) => (
              <select
                className="input"
                id={id}
                value={selectedOrderId}
                onChange={(e) => setSelectedOrderId(e.target.value)}
                style={{ maxWidth: 480 }}
              >
                <option value="">— {t('production.executionCenter.chooseOrder')} —</option>
                {orders.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.number} — {label(o)}
                  </option>
                ))}
              </select>
            )}
          </FormField>
        </Card>
      )}

      {/* ── No order selected ── */}
      {!selectedOrderId && !loading && (
        <Card>
          <div className="stat-card__note">{t('production.executionCenter.noOrderHint')}</div>
        </Card>
      )}

      {/* ── Order selected, loading execution data ── */}
      {selectedOrderId && execLoading && <Card><Spinner /></Card>}

      {/* ── Order selected, data loaded ── */}
      {selectedOrderId && selectedOrder && !execLoading && (
        <>
          {/* Order summary bar */}
          <Card>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-4)', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <strong>{selectedOrder.number}</strong>
                {' — '}
                <StatusBadge status={selectedOrder.status} />
                {' — '}
                {t('production.fields.customerProduct')}: {selectedOrder.customer_product}
                {' — '}
                {selectedOrder.planned_quantity} {selectedOrder.uom}
              </div>
              {selectedOrder.status === 'RELEASED' && canManage && (
                <Button variant="secondary" size="sm" loading={busy} onClick={() => void completeOrder()}>
                  {t('production.actions.complete')}
                </Button>
              )}
            </div>
          </Card>

          {/* ── Forms: issue | register unit | output ── */}
          {selectedOrder.status === 'RELEASED' && canManage && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-4)' }}>
              {/* Material issue form */}
              <Card>
                <h3>{t('production.execution.issueTitle')}</h3>
                <form className="stack" onSubmit={(e) => void postIssue(e)}>
                  {selectField('production.execution.material', issueMaterial, setIssueMaterial, materials)}
                  {selectField('production.execution.warehouse', issueWarehouse, setIssueWarehouse, warehouses)}
                  {selectField('production.execution.uom', issueUom, setIssueUom, uoms)}
                  <FormField label={t('production.execution.method')} required>
                    {({ id }) => (
                      <select
                        className="input"
                        id={id}
                        value={issueMethod}
                        onChange={(e) => setIssueMethod(e.target.value as MaterialIssueMethod)}
                        disabled={busy}
                      >
                        <option value="EXPLICIT">{t('production.execution.methods.EXPLICIT')}</option>
                        <option value="BACKFLUSH">{t('production.execution.methods.BACKFLUSH')}</option>
                      </select>
                    )}
                  </FormField>
                  {issueMethod === 'EXPLICIT' && selectField('production.execution.unit', issueUnit, setIssueUnit, units)}
                  <FormField label={t('production.execution.quantity')} required>
                    {({ id }) => (
                      <Input id={id} type="number" min="0" step="0.000001" value={issueQuantity}
                        onChange={(e) => setIssueQuantity(e.target.value)} required disabled={busy} />
                    )}
                  </FormField>
                  <Button type="submit" loading={busy}>{t('production.execution.postIssue')}</Button>
                </form>
              </Card>

              {/* Register traceability unit form */}
              <Card>
                <h3>{t('production.execution.newUnitTitle')}</h3>
                <form className="stack" onSubmit={(e) => void registerUnit(e)}>
                  <FormField label={t('production.execution.identifier')} required>
                    {({ id }) => (
                      <Input id={id} value={unitIdentifier}
                        onChange={(e) => setUnitIdentifier(e.target.value)} required disabled={busy} />
                    )}
                  </FormField>
                  <FormField label={t('production.execution.unitType')} required>
                    {({ id }) => (
                      <select className="input" id={id} value={unitType}
                        onChange={(e) => setUnitType(e.target.value as TraceabilityUnitType)} disabled={busy}>
                        {UNIT_TYPES.map((typ) => (
                          <option key={typ} value={typ}>{t(`production.execution.unitTypes.${typ}`)}</option>
                        ))}
                      </select>
                    )}
                  </FormField>
                  {selectField('production.execution.material', unitMaterial, setUnitMaterial, materials, false)}
                  <FormField label={t('production.execution.quantity')}>
                    {({ id }) => (
                      <Input id={id} type="number" min="0" step="0.000001" value={unitQuantity}
                        onChange={(e) => setUnitQuantity(e.target.value)} disabled={busy} />
                    )}
                  </FormField>
                  <Button type="submit" variant="secondary" loading={busy}>
                    {t('production.execution.createUnit')}
                  </Button>
                </form>
              </Card>

              {/* Production output form */}
              <Card>
                <h3>{t('production.execution.outputTitle')}</h3>
                <form className="stack" onSubmit={(e) => void postOutput(e)}>
                  {selectField('production.execution.unit', outputUnit, setOutputUnit, units)}
                  {selectField('production.execution.warehouse', outputWarehouse, setOutputWarehouse, warehouses)}
                  {selectField('production.execution.uom', outputUom, setOutputUom, uoms)}
                  <FormField label={t('production.execution.quantity')} required>
                    {({ id }) => (
                      <Input id={id} type="number" min="0" step="0.000001" value={outputQuantity}
                        onChange={(e) => setOutputQuantity(e.target.value)} required disabled={busy} />
                    )}
                  </FormField>
                  <Button type="submit" loading={busy}>{t('production.execution.postOutput')}</Button>
                </form>
              </Card>
            </div>
          )}

          {selectedOrder.status !== 'RELEASED' && (
            <Card>
              <div className="stat-card__note">{t('production.executionCenter.orderNotReleased')}</div>
            </Card>
          )}

          {/* ── Material issues table ── */}
          <Card>
            <h3>{t('production.execution.issuesTitle')}</h3>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('production.execution.method')}</th>
                    <th>{t('production.execution.material')}</th>
                    <th className="text-end">{t('production.execution.quantity')}</th>
                    <th>{t('production.execution.unit')}</th>
                    <th>{t('production.execution.warehouse')}</th>
                  </tr>
                </thead>
                <tbody>
                  {issues.length === 0 ? (
                    <tr><td colSpan={5}>{t('masterData.empty')}</td></tr>
                  ) : (
                    issues.map((iss) => (
                      <tr key={iss.id}>
                        <td>{t(`production.execution.methods.${iss.method}`)}</td>
                        <td>{iss.material}</td>
                        <td className="text-end">{iss.quantity}</td>
                        <td>{iss.traceability_unit ?? '—'}</td>
                        <td>{iss.warehouse}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          {/* ── Production outputs table ── */}
          <Card>
            <h3>{t('production.execution.outputsTitle')}</h3>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="text-end">{t('production.execution.quantity')}</th>
                    <th>{t('production.execution.unit')}</th>
                    <th>{t('production.execution.warehouse')}</th>
                  </tr>
                </thead>
                <tbody>
                  {outputs.length === 0 ? (
                    <tr><td colSpan={3}>{t('masterData.empty')}</td></tr>
                  ) : (
                    outputs.map((out) => (
                      <tr key={out.id}>
                        <td className="text-end">{out.quantity}</td>
                        <td>{out.traceability_unit}</td>
                        <td>{out.warehouse}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}