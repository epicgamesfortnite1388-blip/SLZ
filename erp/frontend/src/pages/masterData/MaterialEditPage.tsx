import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import {
  updateMaterial,
  type Material,
  type Paginated,
} from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

interface CompanyOption {
  id: string;
  code: string;
  name_fa: string;
}

interface UomOption {
  id: string;
  code: string;
  name_fa: string;
}

/** All MaterialSubtype choices (mirrors the backend enum with display labels
 * keyed through i18n — the wire value is the enum member name). */
const SUBTYPE_OPTIONS = [
  'RESIN_MASTERBATCH',
  'INK',
  'SOLVENT',
  'CONSUMABLE',
  'PACKAGING',
  'REGRIND',
  'SEMI_FINISHED',
  'FINISHED',
] as const;

/**
 * Material edit form — replicates the PartnerEditPage PATCH flow for the
 * catalog Material master. `code` stays fixed (business numbers are immutable
 * identities); planning parameters and naming are editable and audited
 * server-side.
 */
export function MaterialEditPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [companies, setCompanies] = useState<CompanyOption[]>([]);
  const [uoms, setUoms] = useState<UomOption[]>([]);

  const [company, setCompany] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [subtype, setSubtype] = useState('RESIN_MASTERBATCH');
  const [baseUom, setBaseUom] = useState('');
  const [msdsRef, setMsdsRef] = useState('');
  const [leadTimeDays, setLeadTimeDays] = useState('');
  const [shelfLifeDays, setShelfLifeDays] = useState('');
  const [reorderPoint, setReorderPoint] = useState('');
  const [safetyStock, setSafetyStock] = useState('');
  const [minStock, setMinStock] = useState('');
  const [maxStock, setMaxStock] = useState('');
  const [isHazardous, setIsHazardous] = useState(false);
  const [isActive, setIsActive] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiClient.get<Material>(`/catalog/materials/${id}/`),
      apiClient.get<Paginated<CompanyOption>>('/organization/companies/?page_size=100'),
      apiClient.get<Paginated<UomOption>>('/catalog/uoms/?page_size=200'),
    ])
      .then(([material, co, uo]) => {
        if (cancelled) return;
        setCode(material.code);
        setNameFa(material.name_fa);
        setNameEn(material.name_en);
        setCompany(material.company);
        setSubtype(material.subtype);
        setBaseUom(material.base_uom ?? '');
        setMsdsRef(material.msds_ref ?? '');
        setLeadTimeDays(material.lead_time_days == null ? '' : String(material.lead_time_days));
        setShelfLifeDays(material.shelf_life_days == null ? '' : String(material.shelf_life_days));
        setReorderPoint(material.reorder_point == null ? '' : String(material.reorder_point));
        setSafetyStock(material.safety_stock == null ? '' : String(material.safety_stock));
        setMinStock(material.min_stock == null ? '' : String(material.min_stock));
        setMaxStock(material.max_stock == null ? '' : String(material.max_stock));
        setIsHazardous(material.is_hazardous);
        setIsActive(material.is_active);
        setCompanies(co.results);
        setUoms(uo.results);
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

  const numOrNull = (s: string): number | null => {
    if (s.trim() === '') return null;
    const v = Number(s);
    return Number.isNaN(v) ? null : v;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await updateMaterial(id, {
        company,
        name_fa: nameFa,
        name_en: nameEn,
        subtype,
        base_uom: baseUom,
        is_hazardous: isHazardous,
        is_active: isActive,
        msds_ref: msdsRef,
        lead_time_days: numOrNull(leadTimeDays),
        shelf_life_days: numOrNull(shelfLifeDays),
        reorder_point: numOrNull(reorderPoint),
        safety_stock: numOrNull(safetyStock),
        min_stock: numOrNull(minStock),
        max_stock: numOrNull(maxStock),
      });
      navigate(`/master-data/materials/${id}`);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

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
        <h1 className="page-header__title">{t('materials.edit')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <FormField label={t('masterData.fields.company')} required>
            {({ id: fieldId }) => (
              <select
                id={fieldId}
                className="input"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                disabled={submitting}
                required
              >
                {companies.length === 0 && <option value="">—</option>}
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name_fa} ({c.code})
                  </option>
                ))}
              </select>
            )}
          </FormField>

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

          <FormField label={t('materials.subtype')} required>
            {({ id: fieldId }) => (
              <select
                id={fieldId}
                className="input"
                value={subtype}
                onChange={(e) => setSubtype(e.target.value)}
                disabled={submitting}
                required
              >
                {SUBTYPE_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {t(`materials.subtypes.${s}`, { defaultValue: s })}
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('masterData.fields.baseUom')} required>
            {({ id: fieldId }) => (
              <select
                id={fieldId}
                className="input"
                value={baseUom}
                onChange={(e) => setBaseUom(e.target.value)}
                disabled={submitting}
                required
              >
                {uoms.length === 0 && <option value="">—</option>}
                {uoms.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name_fa} ({u.code})
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('materials.msdsRef')}>
            {({ id: fieldId }) => (
              <Input id={fieldId} value={msdsRef} onChange={(e) => setMsdsRef(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.leadTimeDays')}>
            {({ id: fieldId }) => (
              <Input id={fieldId} type="number" min="0" value={leadTimeDays} onChange={(e) => setLeadTimeDays(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.shelfLifeDays')}>
            {({ id: fieldId }) => (
              <Input id={fieldId} type="number" min="0" value={shelfLifeDays} onChange={(e) => setShelfLifeDays(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.reorderPoint')}>
            {({ id: fieldId }) => (
              <Input id={fieldId} type="number" step="any" value={reorderPoint} onChange={(e) => setReorderPoint(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.safetyStock')}>
            {({ id: fieldId }) => (
              <Input id={fieldId} type="number" step="any" value={safetyStock} onChange={(e) => setSafetyStock(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.minStock')}>
            {({ id: fieldId }) => (
              <Input id={fieldId} type="number" step="any" value={minStock} onChange={(e) => setMinStock(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.maxStock')}>
            {({ id: fieldId }) => (
              <Input id={fieldId} type="number" step="any" value={maxStock} onChange={(e) => setMaxStock(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <label className="checkbox">
            <input
              type="checkbox"
              checked={isHazardous}
              onChange={(e) => setIsHazardous(e.target.checked)}
              disabled={submitting}
            />
            {t('materials.hazardous')}
          </label>

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
              onClick={() => navigate(`/master-data/materials/${id}`)}
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
