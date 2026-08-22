import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { apiClient } from '@/api/client';
import {
  createMaterialIssue,
  createProductionOutput,
  type MaterialIssue,
  type MaterialIssueMethod,
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
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

interface Option {
  id: string;
  code?: string;
  name_fa?: string;
  name_en?: string;
  traceability_mode?: string;
}

interface Props {
  orderId: string;
  companyId: string;
  customerProductId: string;
  uomId: string;
}

const UNIT_TYPES: TraceabilityUnitType[] = ['BATCH', 'ROLL', 'CARTON', 'PALLET'];

export function ProductionExecutionPanel({
  orderId,
  companyId,
  customerProductId,
  uomId,
}: Props): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canView = hasPermission('production.execution.view');
  const canManage = hasPermission('production.execution.manage');
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [materials, setMaterials] = useState<Option[]>([]);
  const [uoms, setUoms] = useState<Option[]>([]);
  const [units, setUnits] = useState<TraceabilityUnit[]>([]);
  const [issues, setIssues] = useState<MaterialIssue[]>([]);
  const [outputs, setOutputs] = useState<ProductionOutput[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [issueMaterial, setIssueMaterial] = useState('');
  const [issueUnit, setIssueUnit] = useState('');
  const [issueWarehouse, setIssueWarehouse] = useState('');
  const [issueQuantity, setIssueQuantity] = useState('');
  const [issueMethod, setIssueMethod] = useState<MaterialIssueMethod>('EXPLICIT');
  const [issueUom, setIssueUom] = useState(uomId);
  const [outputUnit, setOutputUnit] = useState('');
  const [outputWarehouse, setOutputWarehouse] = useState('');
  const [outputQuantity, setOutputQuantity] = useState('');
  const [outputUom, setOutputUom] = useState(uomId);
  const [unitType, setUnitType] = useState<TraceabilityUnitType>('BATCH');
  const [unitIdentifier, setUnitIdentifier] = useState('');
  const [unitMaterial, setUnitMaterial] = useState('');
  const [unitQuantity, setUnitQuantity] = useState('');

  const label = (option: Option): string => option.name_fa || option.name_en || option.code || option.id;
  const unitLabel = (unit: TraceabilityUnit): string => `${unit.identifier} (${unit.unit_type})`;

  const load = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const [warehouseRes, materialRes, uomRes, unitRes, issueRes, outputRes] = await Promise.all([
        apiClient.get<Paginated<Warehouse>>('/inventory/warehouses/?page_size=100'),
        apiClient.get<Paginated<Option>>('/catalog/materials/?page_size=100'),
        apiClient.get<Paginated<Option>>('/catalog/uoms/?page_size=100'),
        fetchTraceabilityUnits(`?company=${encodeURIComponent(companyId)}&page_size=100`),
        apiClient.get<Paginated<MaterialIssue>>(
          `/production/material-issues/?production_order=${encodeURIComponent(orderId)}&page_size=100`,
        ),
        apiClient.get<Paginated<ProductionOutput>>(
          `/production/outputs/?production_order=${encodeURIComponent(orderId)}&page_size=100`,
        ),
      ]);
      setWarehouses(warehouseRes.results);
      setMaterials(materialRes.results);
      setUoms(uomRes.results);
      setUnits(unitRes.results);
      setIssues(issueRes.results);
      setOutputs(outputRes.results);
      if (!issueWarehouse && warehouseRes.results[0]) setIssueWarehouse(warehouseRes.results[0].id);
      if (!outputWarehouse && warehouseRes.results[0]) setOutputWarehouse(warehouseRes.results[0].id);
      if (!issueMaterial && materialRes.results[0]) setIssueMaterial(materialRes.results[0].id);
      if (!unitMaterial && materialRes.results[0]) setUnitMaterial(materialRes.results[0].id);
      if (!issueUom && uomRes.results[0]) setIssueUom(uomRes.results[0].id);
      if (!outputUom && uomRes.results[0]) setOutputUom(uomRes.results[0].id);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (canView) void load();
    // The order/company identity is stable for this panel instance.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canView, orderId, companyId]);

  if (!canView) return <></>;
  if (loading) return <Card title={t('production.execution.title')}><Spinner /></Card>;

  const select = (
    labelKey: string,
    value: string,
    onChange: (value: string) => void,
    options: Option[] | Warehouse[] | TraceabilityUnit[],
    required = true,
  ): JSX.Element => (
    <FormField label={t(labelKey)} required={required}>
      {({ id }) => (
        <select className="input" id={id} value={value} onChange={(e) => onChange(e.target.value)} required={required} disabled={!canManage || busy}>
          <option value="">—</option>
          {options.map((option) => {
            const item = option as Option & Warehouse & TraceabilityUnit;
            const text = 'identifier' in item ? unitLabel(item) : label(item);
            return <option key={item.id} value={item.id}>{text}</option>;
          })}
        </select>
      )}
    </FormField>
  );

  const postIssue = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await createMaterialIssue({
        production_order: orderId,
        material: issueMaterial,
        traceability_unit: issueMethod === 'EXPLICIT' ? issueUnit : null,
        warehouse: issueWarehouse,
        quantity: issueQuantity,
        uom: issueUom,
        method: issueMethod,
      });
      setIssueQuantity('');
      setIssueUnit('');
      await load();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setBusy(false);
    }
  };

  const postOutput = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await createProductionOutput({
        production_order: orderId,
        traceability_unit: outputUnit,
        warehouse: outputWarehouse,
        quantity: outputQuantity,
        uom: outputUom,
      });
      setOutputQuantity('');
      await load();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setBusy(false);
    }
  };

  const createUnit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const created = await createTraceabilityUnit({
        company: companyId,
        material: unitMaterial || null,
        customer_product_id: customerProductId,
        unit_type: unitType,
        identifier: unitIdentifier,
        quantity: unitQuantity || null,
        uom: outputUom || issueUom || uomId,
      });
      setOutputUnit(created.id);
      setUnitIdentifier('');
      setUnitQuantity('');
      await load();
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title={t('production.execution.title')}>
      {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}
      {canManage && (
        <div className="stack">
          <form className="stack" onSubmit={(event) => void postIssue(event)}>
            <h3>{t('production.execution.issueTitle')}</h3>
            {select('production.execution.material', issueMaterial, setIssueMaterial, materials)}
            {select('production.execution.warehouse', issueWarehouse, setIssueWarehouse, warehouses)}
            <FormField label={t('production.execution.method')} required>
              {({ id }) => (
                <select className="input" id={id} value={issueMethod} onChange={(e) => setIssueMethod(e.target.value as MaterialIssueMethod)} disabled={busy}>
                  <option value="EXPLICIT">{t('production.execution.methods.EXPLICIT')}</option>
                  <option value="BACKFLUSH">{t('production.execution.methods.BACKFLUSH')}</option>
                </select>
              )}
            </FormField>
            {issueMethod === 'EXPLICIT' && select('production.execution.unit', issueUnit, setIssueUnit, units)}
            {select('production.execution.uom', issueUom, setIssueUom, uoms)}
            <FormField label={t('production.execution.quantity')} required>
              {({ id }) => <Input id={id} type="number" min="0" step="0.000001" value={issueQuantity} onChange={(e) => setIssueQuantity(e.target.value)} required disabled={busy} />}
            </FormField>
            <Button type="submit" loading={busy}>{t('production.execution.postIssue')}</Button>
          </form>

          <form className="stack" onSubmit={(event) => void createUnit(event)}>
            <h3>{t('production.execution.newUnitTitle')}</h3>
            <FormField label={t('production.execution.identifier')} required>
              {({ id }) => <Input id={id} value={unitIdentifier} onChange={(e) => setUnitIdentifier(e.target.value)} required disabled={busy} />}
            </FormField>
            <FormField label={t('production.execution.unitType')} required>
              {({ id }) => (
                <select className="input" id={id} value={unitType} onChange={(e) => setUnitType(e.target.value as TraceabilityUnitType)} disabled={busy}>
                  {UNIT_TYPES.map((type) => <option key={type} value={type}>{t(`production.execution.unitTypes.${type}`)}</option>)}
                </select>
              )}
            </FormField>
            {select('production.execution.material', unitMaterial, setUnitMaterial, materials, false)}
            <FormField label={t('production.execution.quantity')}>
              {({ id }) => <Input id={id} type="number" min="0" step="0.000001" value={unitQuantity} onChange={(e) => setUnitQuantity(e.target.value)} disabled={busy} />}
            </FormField>
            <Button type="submit" variant="secondary" loading={busy}>{t('production.execution.createUnit')}</Button>
          </form>

          <form className="stack" onSubmit={(event) => void postOutput(event)}>
            <h3>{t('production.execution.outputTitle')}</h3>
            {select('production.execution.unit', outputUnit, setOutputUnit, units)}
            {select('production.execution.warehouse', outputWarehouse, setOutputWarehouse, warehouses)}
            {select('production.execution.uom', outputUom, setOutputUom, uoms)}
            <FormField label={t('production.execution.quantity')} required>
              {({ id }) => <Input id={id} type="number" min="0" step="0.000001" value={outputQuantity} onChange={(e) => setOutputQuantity(e.target.value)} required disabled={busy} />}
            </FormField>
            <Button type="submit" loading={busy}>{t('production.execution.postOutput')}</Button>
          </form>
        </div>
      )}

      <div className="table-scroll">
        <table className="data-table">
          <caption>{t('production.execution.issuesTitle')}</caption>
          <thead><tr><th>{t('production.execution.method')}</th><th>{t('production.execution.quantity')}</th><th>{t('production.execution.unit')}</th></tr></thead>
          <tbody>{issues.map((issue) => <tr key={issue.id}><td>{t(`production.execution.methods.${issue.method}`)}</td><td>{issue.quantity}</td><td>{issue.traceability_unit ?? '—'}</td></tr>)}</tbody>
        </table>
      </div>
      <div className="table-scroll">
        <table className="data-table">
          <caption>{t('production.execution.outputsTitle')}</caption>
          <thead><tr><th>{t('production.execution.quantity')}</th><th>{t('production.execution.unit')}</th><th>{t('production.execution.warehouse')}</th></tr></thead>
          <tbody>{outputs.map((output) => <tr key={output.id}><td>{output.quantity}</td><td>{output.traceability_unit}</td><td>{output.warehouse}</td></tr>)}</tbody>
        </table>
      </div>
    </Card>
  );
}
