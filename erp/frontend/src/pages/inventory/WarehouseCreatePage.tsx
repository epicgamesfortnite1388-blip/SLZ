import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import {
  createWarehouse,
  WAREHOUSE_STORE_TYPES,
  type WarehouseStoreType,
} from '@/api/inventory';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Warehouse create form — the representative audited write flow for Task 007
 * (POST → domain event → audit). Business rules (unique code per company,
 * referential integrity, valid store type) are enforced server-side; the UI
 * surfaces the backend's 400 rather than duplicating the rule.
 */
export function WarehouseCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<Option[]>([]);
  const [sites, setSites] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [site, setSite] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [storeType, setStoreType] = useState<WarehouseStoreType>('GENERAL');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = (path: string, set: (v: Option[]) => void, pick?: (f: Option) => void): void => {
      apiClient
        .get<Paginated<Option>>(`${path}?page_size=100`)
        .then((res) => {
          if (cancelled) return;
          set(res.results);
          if (pick && res.results.length > 0) pick(res.results[0]);
        })
        .catch(() => {
          /* Non-fatal: field stays empty and the user sees a validation error. */
        });
    };
    load('/organization/companies/', setCompanies, (f) => setCompany(f.id));
    load('/organization/sites/', setSites);
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createWarehouse({
        company,
        site: site || null,
        code,
        name_fa: nameFa,
        name_en: nameEn,
        store_type: storeType,
      });
      navigate('/inventory/warehouses');
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
      {({ id }) => (
        <select
          id={id}
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

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('inventory.warehouses.new')}</h1>
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

          <FormField label={t('masterData.fields.code')} required>
            {({ id }) => (
              <Input
                id={id}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          <FormField label={t('masterData.fields.nameFa')} required>
            {({ id }) => (
              <Input
                id={id}
                value={nameFa}
                onChange={(e) => setNameFa(e.target.value)}
                disabled={submitting}
                required
              />
            )}
          </FormField>

          <FormField label={t('masterData.fields.nameEn')}>
            {({ id }) => (
              <Input
                id={id}
                value={nameEn}
                onChange={(e) => setNameEn(e.target.value)}
                disabled={submitting}
              />
            )}
          </FormField>

          <FormField label={t('inventory.fields.storeType')} required>
            {({ id }) => (
              <select
                id={id}
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

          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              {t('masterData.save')}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/inventory/warehouses')}
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
