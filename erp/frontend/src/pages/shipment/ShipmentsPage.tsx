import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { apiClient } from '@/api/client';
import {
  fetchShipments,
  createShipment,
  fetchAllocations,
  type Shipment,
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
  identifier?: string;
  number?: string;
  email?: string;
}

export function ShipmentsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canView = hasPermission('shipment.delivery.view');
  const canManage = hasPermission('shipment.delivery.manage');
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  // Create form state
  const [company, setCompany] = useState('');
  const [warehouse, setWarehouse] = useState('');
  const [customer, setCustomer] = useState('');
  const [salesOrder, setSalesOrder] = useState('');
  const [number, setNumber] = useState('');
  const [shippedAt, setShippedAt] = useState(new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState('');
  // Lines state
  const [lines, setLines] = useState<
    Array<{ traceability_unit: string; allocation: string; quantity: string; uom: string }>
  >([{ traceability_unit: '', allocation: '', quantity: '', uom: '' }]);

  // Ref data
  const [companies, setCompanies] = useState<Option[]>([]);
  const [warehouses, setWarehouses] = useState<Option[]>([]);
  const [customers, setCustomers] = useState<Option[]>([]);
  const [salesOrders, setSalesOrders] = useState<Option[]>([]);
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [units, setUnits] = useState<TraceabilityUnit[]>([]);
  const [uoms, setUoms] = useState<Option[]>([]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [shps, cos, whs, cus, sos, allocResp, unts, ums] = await Promise.all([
        fetchShipments('?page_size=100'),
        apiClient.get<Paginated<Option>>('/organization/companies/?page_size=100'),
        apiClient.get<Paginated<Option>>('/inventory/warehouses/?page_size=100'),
        apiClient.get<Paginated<Option>>('/partners/customers/?page_size=100'),
        apiClient.get<Paginated<Option>>('/sales/orders/?page_size=100'),
        fetchAllocations('?page_size=200&status=RESERVED'),
        fetchTraceabilityUnits('?page_size=200'),
        apiClient.get<Paginated<Option>>('/catalog/uoms/?page_size=100'),
      ]);
      setShipments(shps.results);
      setCompanies(cos.results);
      setWarehouses(whs.results);
      setCustomers(cus.results);
      setSalesOrders(sos.results);
      setAllocations(allocResp.results);
      setUnits(unts.results);
      setUoms(ums.results);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (canView) void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canView]);

  const postShipment = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await createShipment({
        company,
        warehouse,
        customer,
        sales_order: salesOrder || null,
        number,
        shipped_at: shippedAt,
        notes,
        lines: lines.map((ln) => ({
          traceability_unit: ln.traceability_unit,
          allocation: ln.allocation || null,
          quantity: ln.quantity,
          uom: ln.uom,
        })),
      });
      setShowForm(false);
      setNumber('');
      setLines([{ traceability_unit: '', allocation: '', quantity: '', uom: '' }]);
      await load();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setBusy(false);
    }
  };

  const updateLine = (i: number, field: string, value: string) => {
    setLines((prev) => prev.map((ln, idx) => (idx === i ? { ...ln, [field]: value } : ln)));
  };

  const addLine = () => {
    setLines((prev) => [...prev, { traceability_unit: '', allocation: '', quantity: '', uom: '' }]);
  };

  const removeLine = (i: number) => {
    setLines((prev) => prev.filter((_, idx) => idx !== i));
  };

  if (!canView) return <></>;

  if (loading) {
    return (
      <div className="stack">
        <div className="page-header">
          <h1 className="page-header__title">{t('shipment.deliveries.title')}</h1>
        </div>
        <Card>
          <Spinner />
        </Card>
      </div>
    );
  }

  const optLabel = (o: Option): string => o.name_fa || o.identifier || o.code || o.number || o.email || o.id;

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('shipment.deliveries.title')}</h1>
        <p className="page-header__subtitle">{t('shipment.deliveries.subtitle')}</p>
      </div>

      <Card>
        {error && (
          <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {canManage && (
          <div style={{ marginBottom: 'var(--space-5)' }}>
            {!showForm ? (
              <Button onClick={() => setShowForm(true)}>{t('shipment.deliveries.new')}</Button>
            ) : (
              <form className="stack" onSubmit={(e) => void postShipment(e)}>
                <h3>{t('shipment.deliveries.new')}</h3>
                <div className="form-grid">
                  <FormField label={t('shipment.fields.company')} required>
                    {({ id }) => (
                      <select
                        className="input"
                        id={id}
                        value={company}
                        onChange={(e) => setCompany(e.target.value)}
                        required
                        disabled={busy}
                      >
                        <option value="">—</option>
                        {companies.map((c) => (
                          <option key={c.id} value={c.id}>
                            {optLabel(c)}
                          </option>
                        ))}
                      </select>
                    )}
                  </FormField>
                  <FormField label={t('shipment.fields.warehouse')} required>
                    {({ id }) => (
                      <select
                        className="input"
                        id={id}
                        value={warehouse}
                        onChange={(e) => setWarehouse(e.target.value)}
                        required
                        disabled={busy}
                      >
                        <option value="">—</option>
                        {warehouses.map((w) => (
                          <option key={w.id} value={w.id}>
                            {optLabel(w)}
                          </option>
                        ))}
                      </select>
                    )}
                  </FormField>
                  <FormField label={t('shipment.fields.customer')} required>
                    {({ id }) => (
                      <select
                        className="input"
                        id={id}
                        value={customer}
                        onChange={(e) => setCustomer(e.target.value)}
                        required
                        disabled={busy}
                      >
                        <option value="">—</option>
                        {customers.map((c) => (
                          <option key={c.id} value={c.id}>
                            {optLabel(c)}
                          </option>
                        ))}
                      </select>
                    )}
                  </FormField>
                  <FormField label={t('shipment.fields.number')} required>
                    {({ id }) => (
                      <Input
                        id={id}
                        value={number}
                        onChange={(e) => setNumber(e.target.value)}
                        required
                        disabled={busy}
                      />
                    )}
                  </FormField>
                  <FormField label={t('shipment.fields.shippedAt')} required>
                    {({ id }) => (
                      <Input
                        id={id}
                        type="date"
                        value={shippedAt}
                        onChange={(e) => setShippedAt(e.target.value)}
                        required
                        disabled={busy}
                      />
                    )}
                  </FormField>
                  <FormField label={t('sales.fields.notes')}>
                    {({ id }) => (
                      <Input
                        id={id}
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        disabled={busy}
                      />
                    )}
                  </FormField>
                  <FormField label={t('shipment.fields.salesOrder')}>
                    {({ id }) => (
                      <select
                        className="input"
                        id={id}
                        value={salesOrder}
                        onChange={(e) => setSalesOrder(e.target.value)}
                        disabled={busy}
                      >
                        <option value="">—</option>
                        {salesOrders.map((so) => (
                          <option key={so.id} value={so.id}>
                            {optLabel(so)}
                          </option>
                        ))}
                      </select>
                    )}
                  </FormField>
                </div>

                {/* Line items */}
                <fieldset>
                  <legend>{t('shipment.deliveries.lines')}</legend>
                  {lines.map((ln, i) => (
                    <div key={i} className="form-grid" style={{ marginBottom: 'var(--space-3)' }}>
                      <FormField label={t('shipment.fields.unit')} required>
                        {({ id }) => (
                          <select
                            className="input"
                            id={id}
                            value={ln.traceability_unit}
                            onChange={(e) => updateLine(i, 'traceability_unit', e.target.value)}
                            required
                            disabled={busy}
                          >
                            <option value="">—</option>
                            {units.map((u) => (
                              <option key={u.id} value={u.id}>
                                {u.identifier}
                              </option>
                            ))}
                          </select>
                        )}
                      </FormField>
                      <FormField label={t('shipment.fields.allocation')}>
                        {({ id }) => (
                          <select
                            className="input"
                            id={id}
                            value={ln.allocation}
                            onChange={(e) => updateLine(i, 'allocation', e.target.value)}
                            disabled={busy}
                          >
                            <option value="">—</option>
                            {allocations
                              .filter(
                                (a) =>
                                  !ln.traceability_unit ||
                                  a.traceability_unit === ln.traceability_unit,
                              )
                              .map((a) => (
                                <option key={a.id} value={a.id}>
                                  {a.id} — {a.quantity}
                                </option>
                              ))}
                          </select>
                        )}
                      </FormField>
                      <FormField label={t('shipment.fields.quantity')} required>
                        {({ id }) => (
                          <Input
                            id={id}
                            type="number"
                            min="0"
                            step="0.000001"
                            value={ln.quantity}
                            onChange={(e) => updateLine(i, 'quantity', e.target.value)}
                            required
                            disabled={busy}
                          />
                        )}
                      </FormField>
                      <FormField label={t('shipment.fields.uom')} required>
                        {({ id }) => (
                          <select
                            className="input"
                            id={id}
                            value={ln.uom}
                            onChange={(e) => updateLine(i, 'uom', e.target.value)}
                            required
                            disabled={busy}
                          >
                            <option value="">—</option>
                            {uoms.map((u) => (
                              <option key={u.id} value={u.id}>
                                {optLabel(u)}
                              </option>
                            ))}
                          </select>
                        )}
                      </FormField>
                      <div style={{ display: 'flex', alignItems: 'end', gap: 'var(--space-2)' }}>
                        {lines.length > 1 && (
                          <Button
                            type="button"
                            variant="danger"
                            size="sm"
                            disabled={busy}
                            onClick={() => removeLine(i)}
                          >
                            ✕
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                  <Button type="button" variant="secondary" size="sm" disabled={busy} onClick={addLine}>
                    + {t('common.addLine')}
                  </Button>
                </fieldset>

                <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                  <Button type="submit" loading={busy}>
                    {t('masterData.save')}
                  </Button>
                  <Button type="button" variant="secondary" disabled={busy} onClick={() => setShowForm(false)}>
                    {t('common.cancel')}
                  </Button>
                </div>
              </form>
            )}
          </div>
        )}

        {/* Shipments table */}
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('shipment.fields.number')}</th>
                <th>{t('shipment.fields.customer')}</th>
                <th>{t('shipment.fields.shippedAt')}</th>
                <th className="text-end">{t('shipment.fields.lineCount')}</th>
                <th>{t('shipment.fields.status')}</th>
              </tr>
            </thead>
            <tbody>
              {shipments.length === 0 ? (
                <tr>
                  <td colSpan={5}>{t('masterData.empty')}</td>
                </tr>
              ) : (
                shipments.map((s) => (
                  <tr key={s.id}>
                    <td>{s.number}</td>
                    <td>{s.customer}</td>
                    <td>{s.shipped_at}</td>
                    <td className="text-end">{s.lines.length}</td>
                    <td>
                      <StatusBadge status={s.status} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}