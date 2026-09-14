import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import {
  updateWarehouse,
  WAREHOUSE_STORE_TYPES,
  type Warehouse,
  type WarehouseStoreType,
} from '@/api/inventory';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Warehouse edit form — replicates the PartnerEditPage PATCH flow for the
 * inventory Warehouse master. `code` stays fixed (business numbers are
 * immutable identities); naming, site, and store type are editable and audited
 * server-side.
 */
export function WarehouseEditPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [companies, setCompanies] = useState<Option[]>([]);
  const [sites, setSites] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [site, setSite] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [storeType, setStoreType] = useState<WarehouseStoreType>('GENERAL');
  const [notes, setNotes] = useState('');
  const [isActive, setIsActive] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiClient.get<Warehouse>(`/inventory/warehouses/${id}/`),
      apiClient.get<Paginated<Option>>('/organization/companies/?page_size=100'),
      apiClient.get<Paginated<Option>>('/organization/sites/?page_size=200'),
    ])
      .then(([warehouse, co, si]) => {
        if (cancelled) return;
        setCompany(warehouse.company);
        setSite(warehouse.site ?? '');
        setCode(warehouse.code);
        setNameFa(warehouse.name_fa);
        setNameEn(warehouse.name_en ?? '');
        setStoreType(warehouse.store_type);
        setNotes(warehouse.notes ?? '');
        setIsActive(warehouse.is_active);
        setCompanies(co.results);
        setSites(si.results);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setLoadError(isApiError(err) ? err.message : t('common.error'));
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id, t]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await updateWarehouse(id, {
        company,
        site: site || null,
        name_fa: nameFa,
        name_en: nameEn,
        store_type: storeType,
        notes,
        is_active: isActive,
      });
      navigate(`/inventory/warehouses/${id}`);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const orgSelect = (
    labelKey: string,
    value: string,
    onChange: (v: string) => void,
    options: Option[],
    required: boolean,
  ): JSX.Element => (
    <FormField label={t(labelKey)} required={required}>
      {({ id: fieldId }) => (
        <select
          id={fieldId}
          className="input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={submitting}
          required={required}
        >
          <option value="">—</option>
          {options.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name_fa} ({o.code})
            </option>
          ))}
        </select>
      )}
    </FormField>
  );

  if (loading) {
    return (
      <div className="table-state">
        <Spinner label={t('common.loading')} />
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="stack">
        <Alert variant="danger" title={t('common.error')}>
          <p>{loadError}</p>
          <Button variant="secondary" size="sm" onClick={() => window.history.back()}>
            {t('common.back')}
          </Button>
        </Alert>
      </div>
    );
  }

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('inventory.warehouses.edit')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {orgSelect('masterData.fields.company', company, setCompany, companies, true)}
          {orgSelect('inventory.fields.site', site, setSite, sites, false)}

          <FormField label={t('masterData.fields.code')}>
            {({ id: fieldId }) => <Input id={fieldId} value={code} disabled readOnly />}
          </FormField>

          <FormField label={t('masterData.fields.nameFa')} required>
            {({ id: fieldId }) => (
              <Input
                id={fieldId}
                value={nameFa}
                onChange={(e) => setNameFa(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          <FormField label={t('masterData.fields.nameEn')}>
            {({ id: fieldId }) => (
              <Input
                id={fieldId}
                value={nameEn}
                onChange={(e) => setNameEn(e.target.value)}
                disabled={submitting}
              />
            )}
          </FormField>

          <FormField label={t('inventory.fields.storeType')} required>
            {({ id: fieldId }) => (
              <select
                id={fieldId}
                className="input"
                value={storeType}
                onChange={(e) => setStoreType(e.target.value as WarehouseStoreType)}
                disabled={submitting}
                required
              >
                {WAREHOUSE_STORE_TYPES.map((s) => (
                  <option key={s} value={s}>
                    {t(`inventory.storeTypes.${s}`)}
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('inventory.fields.notes')}>
            {({ id: fieldId }) => (
              <Input id={fieldId} value={notes} onChange={(e) => setNotes(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <label className="checkbox">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              disabled={submitting}
            />
            {t('masterData.fields.active')}
          </label>

          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              {t('masterData.save')}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate(`/inventory/warehouses/${id}`)}
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
