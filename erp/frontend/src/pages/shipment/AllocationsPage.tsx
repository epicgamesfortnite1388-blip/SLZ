import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { apiClient } from '@/api/client';
import {
  fetchAllocations,
  createAllocation,
  releaseAllocation,
  type Allocation,
} from '@/api/shipment';
import { fetchTraceabilityUnits, type TraceabilityUnit } from '@/api/inventory';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner, StatusBadge } from '@/components/ui';
import type { Paginated } from '@/api/inventory';

interface Option {
  id: string;
  code?: string;
  name_fa?: string;
  number?: string;
}

export function AllocationsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canView = hasPermission('shipment.allocation.view');
  const canManage = hasPermission('shipment.allocation.manage');
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [company, setCompany] = useState('');
  const [orderLine, setOrderLine] = useState('');
  const [unit, setUnit] = useState('');
  const [qty, setQty] = useState('');
  const [uom, setUom] = useState('');
  const [companies, setCompanies] = useState<Option[]>([]);
  const [orderLines, setOrderLines] = useState<Option[]>([]);
  const [units, setUnits] = useState<TraceabilityUnit[]>([]);
  const [uoms, setUoms] = useState<Option[]>([]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [allocs, cos, ords, unts, ums] = await Promise.all([
        fetchAllocations('?page_size=100'),
        apiClient.get<Paginated<Option>>('/organization/companies/?page_size=100'),
        apiClient.get<Paginated<Option>>('/sales/order-lines/?page_size=200'),
        fetchTraceabilityUnits('?page_size=200'),
        apiClient.get<Paginated<Option>>('/catalog/uoms/?page_size=100'),
      ]);
      setAllocations(allocs.results);
      setCompanies(cos.results);
      setOrderLines(ords.results);
      setUnits(unts.results);
      setUoms(ums.results);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (canView) void load(); }, [canView]); // eslint-disable-line react-hooks/exhaustive-deps

  const postAlloc = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await createAllocation({
        company,
        sales_order_line: orderLine,
        traceability_unit: unit,
        quantity: qty,
        uom,
      });
      setQty('');
      await load();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally { setBusy(false); }
  };

  const doRelease = async (id: string) => {
    setBusy(true);
    setError(null);
    try {
      await releaseAllocation(id);
      await load();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally { setBusy(false); }
  };

  if (!canView) return <></>;
  if (loading) {
    return (
      <div className="stack">
        <div className="page-header">
          <h1 className="page-header__title">{t('shipment.allocations.title')}</h1>
        </div>
        <Card><Spinner /></Card>
      </div>
    );
  }

  const optLabel = (o: Option): string => o.name_fa || o.code || o.number || o.id;

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('shipment.allocations.title')}</h1>
        <p className="page-header__subtitle">{t('shipment.allocations.subtitle')}</p>
      </div>

      <Card>
        {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}

        {canManage && (
          <form className="stack" onSubmit={(e) => void postAlloc(e)} style={{ marginBottom: 'var(--space-5)' }}>
            <h3>{t('shipment.allocations.new')}</h3>
            <div className="form-grid">
              <FormField label={t('shipment.fields.company')} required>
                {({ id }) => <select className="input" id={id} value={company} onChange={(e) => setCompany(e.target.value)} required disabled={busy}><option value="">—</option>{companies.map((c) => <option key={c.id} value={c.id}>{optLabel(c)}</option>)}</select>}
              </FormField>
              <FormField label={t('shipment.fields.orderLine')} required>
                {({ id }) => <select className="input" id={id} value={orderLine} onChange={(e) => setOrderLine(e.target.value)} required disabled={busy}><option value="">—</option>{orderLines.map((ol) => <option key={ol.id} value={ol.id}>{ol.id}</option>)}</select>}
              </FormField>
              <FormField label={t('shipment.fields.unit')} required>
                {({ id }) => <select className="input" id={id} value={unit} onChange={(e) => setUnit(e.target.value)} required disabled={busy}><option value="">—</option>{units.map((u) => <option key={u.id} value={u.id}>{u.identifier}</option>)}</select>}
              </FormField>
              <FormField label={t('shipment.fields.uom')} required>
                {({ id }) => <select className="input" id={id} value={uom} onChange={(e) => setUom(e.target.value)} required disabled={busy}><option value="">—</option>{uoms.map((u) => <option key={u.id} value={u.id}>{optLabel(u)}</option>)}</select>}
              </FormField>
              <FormField label={t('shipment.fields.quantity')} required>
                {({ id }) => <Input id={id} type="number" min="0" step="0.000001" value={qty} onChange={(e) => setQty(e.target.value)} required disabled={busy} />}
              </FormField>
            </div>
            <Button type="submit" loading={busy}>{t('masterData.save')}</Button>
          </form>
        )}

        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('shipment.fields.unit')}</th>
                <th className="text-end">{t('shipment.fields.quantity')}</th>
                <th>{t('shipment.fields.status')}</th>
                <th>{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {allocations.length === 0 ? (
                <tr><td colSpan={4}>{t('masterData.empty')}</td></tr>
              ) : allocations.map((a) => (
                <tr key={a.id}>
                  <td>{a.traceability_unit}</td>
                  <td className="text-end">{a.quantity}</td>
                  <td><StatusBadge status={a.status} /></td>
                  <td>
                    {a.status === 'RESERVED' && canManage && (
                      <Button size="sm" variant="secondary" loading={busy} onClick={() => void doRelease(a.id)}>
                        {t('shipment.actions.release')}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}