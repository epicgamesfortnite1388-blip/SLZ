import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import type { Paginated } from '@/api/masterData';
import { createPlanningPolicy } from '@/api/planning';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface IdName {
  id: string;
  code: string;
  name_fa: string;
  company?: string;
  material?: string | null;
}

/**
 * Create a reorder policy: company + warehouse + exactly one item (purchased
 * material XOR manufactured customer product) + min/max replenishment levels.
 * The engine suggests; this record only declares intent — no order is created.
 */
export function PlanningPolicyCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<IdName[]>([]);
  const [warehouses, setWarehouses] = useState<IdName[]>([]);
  const [materials, setMaterials] = useState<IdName[]>([]);
  const [products, setProducts] = useState<IdName[]>([]);

  const [company, setCompany] = useState('');
  const [warehouse, setWarehouse] = useState('');
  const [itemKind, setItemKind] = useState<'MATERIAL' | 'PRODUCT'>('MATERIAL');
  const [material, setMaterial] = useState('');
  const [product, setProduct] = useState('');
  const [reorderPoint, setReorderPoint] = useState('');
  const [targetLevel, setTargetLevel] = useState('');
  const [safetyStock, setSafetyStock] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<Paginated<IdName>>('/organization/companies/?page_size=200')
      .then((res) => {
        if (cancelled) return;
        setCompanies(res.results);
        if (res.results.length > 0) setCompany(res.results[0].id);
      })
      .catch(() => {});
    apiClient
      .get<Paginated<IdName>>('/catalog/materials/?page_size=200')
      .then((res) => {
        if (!cancelled) setMaterials(res.results);
      })
      .catch(() => {});
    apiClient
      .get<Paginated<IdName>>('/engineering/customer-products/?page_size=200')
      .then((res) => {
        if (!cancelled) setProducts(res.results);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  // Warehouses are company-scoped: reload candidates when the company changes.
  useEffect(() => {
    let cancelled = false;
    setWarehouse('');
    const qs = company ? `?company=${encodeURIComponent(company)}&page_size=200` : '?page_size=200';
    apiClient
      .get<Paginated<IdName>>(`/inventory/warehouses/${qs}`)
      .then((res) => {
        if (!cancelled) setWarehouses(res.results);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [company]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    if (itemKind === 'MATERIAL' && !material) {
      setError(t('planning.policies.errors.itemRequired'));
      return;
    }
    if (itemKind === 'PRODUCT' && !product) {
      setError(t('planning.policies.errors.itemRequired'));
      return;
    }
    setSubmitting(true);
    try {
      await createPlanningPolicy({
        company,
        warehouse,
        material: itemKind === 'MATERIAL' ? material : null,
        customer_product: itemKind === 'PRODUCT' ? product : null,
        reorder_point: reorderPoint,
        target_level: targetLevel,
        safety_stock: safetyStock || null,
      });
      navigate('/planning/policies');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const optionLabel = (o: IdName): string => `${o.name_fa}${o.code ? ` (${o.code})` : ''}`;
  const companyWarehouses = warehouses;

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('planning.policies.new')}</h1>
      </div>
      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <FormField label={t('masterData.fields.company')} required>
            {({ id }) => (
              <select
                id={id}
                className="input"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                disabled={submitting}
                required
              >
                <option value="">—</option>
                {companies.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name_fa} ({o.code})
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('planning.fields.warehouse')} required>
            {({ id }) => (
              <select
                id={id}
                className="input"
                value={warehouse}
                onChange={(e) => setWarehouse(e.target.value)}
                disabled={submitting}
                required
              >
                <option value="">—</option>
                {companyWarehouses.map((o) => (
                  <option key={o.id} value={o.id}>
                    {optionLabel(o)}
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('planning.fields.itemType')} required>
            {() => (
              <div className="field-row">
                {(['MATERIAL', 'PRODUCT'] as const).map((kind) => (
                  <label key={kind} style={{ display: 'inline-flex', gap: 'var(--space-2)', alignItems: 'center' }}>
                    <input
                      type="radio"
                      name="item-kind"
                      checked={itemKind === kind}
                      onChange={() => setItemKind(kind)}
                      disabled={submitting}
                    />
                    {t(`planning.itemTypes.${kind}`)}
                  </label>
                ))}
              </div>
            )}
          </FormField>

          {itemKind === 'MATERIAL' ? (
            <FormField label={t('planning.fields.material')} required>
              {({ id }) => (
                <select
                  id={id}
                  className="input"
                  value={material}
                  onChange={(e) => setMaterial(e.target.value)}
                  disabled={submitting}
                  required
                >
                  <option value="">—</option>
                  {materials.map((o) => (
                    <option key={o.id} value={o.id}>
                      {optionLabel(o)}
                    </option>
                  ))}
                </select>
              )}
            </FormField>
          ) : (
            <FormField label={t('planning.fields.customerProduct')} required>
              {({ id }) => (
                <select
                  id={id}
                  className="input"
                  value={product}
                  onChange={(e) => setProduct(e.target.value)}
                  disabled={submitting}
                  required
                >
                  <option value="">—</option>
                  {products.map((o) => (
                    <option key={o.id} value={o.id}>
                      {optionLabel(o)}
                    </option>
                  ))}
                </select>
              )}
            </FormField>
          )}

          <div className="field-row">
            <FormField label={t('planning.fields.reorderPoint')} required>
              {({ id }) => (
                <Input
                  id={id}
                  type="number"
                  step="any"
                  min="0"
                  value={reorderPoint}
                  onChange={(e) => setReorderPoint(e.target.value)}
                  disabled={submitting}
                  required
                />
              )}
            </FormField>
            <FormField label={t('planning.fields.targetLevel')} required>
              {({ id }) => (
                <Input
                  id={id}
                  type="number"
                  step="any"
                  min="0"
                  value={targetLevel}
                  onChange={(e) => setTargetLevel(e.target.value)}
                  disabled={submitting}
                  required
                />
              )}
            </FormField>
          </div>

          <FormField label={t('planning.fields.safetyStock')}>
            {({ id }) => (
              <Input
                id={id}
                type="number"
                step="any"
                min="0"
                value={safetyStock}
                onChange={(e) => setSafetyStock(e.target.value)}
                disabled={submitting}
              />
            )}
          </FormField>

          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              {t('masterData.save')}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/planning/policies')}
              disabled={submitting}
            >
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
