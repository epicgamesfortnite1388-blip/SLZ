import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { createMaterial, type Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input } from '@/components/ui';

interface CompanyOption {
  id: string;
  code: string;
  name_fa: string;
  name_en: string;
}

interface UomOption {
  id: string;
  code: string;
  name_fa: string;
  name_en: string;
  dimension: string;
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
 * Material create form — the write flow for the catalog Material master. Like
 * the partner form, the POST routes through the audited service layer and the
 * backend's validation messages are surfaced directly on the form.
 */
export function MaterialCreatePage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [companies, setCompanies] = useState<CompanyOption[]>([]);
  const [uoms, setUoms] = useState<UomOption[]>([]);

  const [company, setCompany] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [subtype, setSubtype] = useState('RESIN_MASTERBATCH');
  const [baseUom, setBaseUom] = useState('');
  const [isHazardous, setIsHazardous] = useState(false);
  const [msdsRef, setMsdsRef] = useState('');
  const [leadTimeDays, setLeadTimeDays] = useState('');
  const [shelfLifeDays, setShelfLifeDays] = useState('');
  const [reorderPoint, setReorderPoint] = useState('');
  const [safetyStock, setSafetyStock] = useState('');
  const [minStock, setMinStock] = useState('');
  const [maxStock, setMaxStock] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiClient.get<Paginated<CompanyOption>>('/organization/companies/?page_size=100'),
      apiClient.get<Paginated<UomOption>>('/catalog/uoms/?page_size=200'),
    ])
      .then(([co, uo]) => {
        if (cancelled) return;
        setCompanies(co.results);
        if (co.results.length > 0) setCompany(co.results[0].id);
        setUoms(uo.results);
        if (uo.results.length > 0) setBaseUom(uo.results[0].id);
      })
      .catch(() => { /* non-fatal */ });
    return () => { cancelled = true; };
  }, []);

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
      await createMaterial({
        company,
        code,
        name_fa: nameFa,
        name_en: nameEn,
        subtype,
        base_uom: baseUom,
        is_hazardous: isHazardous,
        msds_ref: msdsRef,
        lead_time_days: numOrNull(leadTimeDays),
        shelf_life_days: numOrNull(shelfLifeDays),
        reorder_point: numOrNull(reorderPoint),
        safety_stock: numOrNull(safetyStock),
        min_stock: numOrNull(minStock),
        max_stock: numOrNull(maxStock),
      });
      navigate('/master-data/materials');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('materials.new')}</h1>
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
                {companies.length === 0 && <option value="">—</option>}
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name_fa} ({c.code})
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <FormField label={t('masterData.fields.code')} required>
            {({ id }) => (
              <Input id={id} value={code} onChange={(e) => setCode(e.target.value)} disabled={submitting} required />
            )}
          </FormField>

          <FormField label={t('masterData.fields.nameFa')} required>
            {({ id }) => (
              <Input id={id} value={nameFa} onChange={(e) => setNameFa(e.target.value)} disabled={submitting} required />
            )}
          </FormField>

          <FormField label={t('masterData.fields.nameEn')}>
            {({ id }) => (
              <Input id={id} value={nameEn} onChange={(e) => setNameEn(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.subtype')} required>
            {({ id }) => (
              <select
                id={id}
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
            {({ id }) => (
              <select
                id={id}
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
            {({ id }) => (
              <Input id={id} value={msdsRef} onChange={(e) => setMsdsRef(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.leadTimeDays')}>
            {({ id }) => (
              <Input id={id} type="number" min="0" value={leadTimeDays} onChange={(e) => setLeadTimeDays(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.shelfLifeDays')}>
            {({ id }) => (
              <Input id={id} type="number" min="0" value={shelfLifeDays} onChange={(e) => setShelfLifeDays(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.reorderPoint')}>
            {({ id }) => (
              <Input id={id} type="number" step="any" value={reorderPoint} onChange={(e) => setReorderPoint(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.safetyStock')}>
            {({ id }) => (
              <Input id={id} type="number" step="any" value={safetyStock} onChange={(e) => setSafetyStock(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.minStock')}>
            {({ id }) => (
              <Input id={id} type="number" step="any" value={minStock} onChange={(e) => setMinStock(e.target.value)} disabled={submitting} />
            )}
          </FormField>

          <FormField label={t('materials.maxStock')}>
            {({ id }) => (
              <Input id={id} type="number" step="any" value={maxStock} onChange={(e) => setMaxStock(e.target.value)} disabled={submitting} />
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

          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              {t('masterData.save')}
            </Button>
            <Button type="button" variant="secondary" onClick={() => navigate('/master-data/materials')} disabled={submitting}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}