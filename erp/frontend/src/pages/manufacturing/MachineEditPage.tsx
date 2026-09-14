import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { updateMachine, type Machine } from '@/api/manufacturing';
import type { Paginated } from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

interface Option {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Machine edit form — replicates the PartnerEditPage PATCH flow for the
 * manufacturing Machine master. `code` stays fixed (business numbers are
 * immutable identities); naming, site, work-center assignment, and the
 * capability profile are editable and audited server-side.
 */
export function MachineEditPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [companies, setCompanies] = useState<Option[]>([]);
  const [sites, setSites] = useState<Option[]>([]);
  const [workCenters, setWorkCenters] = useState<Option[]>([]);

  const [company, setCompany] = useState('');
  const [site, setSite] = useState('');
  const [workCenter, setWorkCenter] = useState('');
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [capabilityProfile, setCapabilityProfile] = useState('');
  const [isActive, setIsActive] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiClient.get<Machine>(`/manufacturing/machines/${id}/`),
      apiClient.get<Paginated<Option>>('/organization/companies/?page_size=200'),
      apiClient.get<Paginated<Option>>('/organization/sites/?page_size=200'),
      apiClient.get<Paginated<Option>>('/manufacturing/work-centers/?page_size=200'),
    ])
      .then(([machine, co, si, wc]) => {
        if (cancelled) return;
        setCompany(machine.company);
        setSite(machine.site ?? '');
        setWorkCenter(machine.work_center ?? '');
        setCode(machine.code);
        setNameFa(machine.name_fa);
        setNameEn(machine.name_en ?? '');
        setCapabilityProfile(
          machine.capability_profile && Object.keys(machine.capability_profile).length > 0
            ? JSON.stringify(machine.capability_profile, null, 2)
            : '',
        );
        setIsActive(machine.is_active);
        setCompanies(co.results);
        setSites(si.results);
        setWorkCenters(wc.results);
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

    let profile: Record<string, unknown> = {};
    if (capabilityProfile.trim() !== '') {
      try {
        profile = JSON.parse(capabilityProfile) as Record<string, unknown>;
      } catch {
        setError(t('manufacturing.machines.invalidProfileJson'));
        return;
      }
    }

    setSubmitting(true);
    try {
      await updateMachine(id, {
        company,
        site: site || null,
        work_center: workCenter || undefined,
        name_fa: nameFa,
        name_en: nameEn,
        capability_profile: profile,
        is_active: isActive,
      });
      navigate(`/manufacturing/machines/${id}`);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const selectField = (
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
        <h1 className="page-header__title">{t('manufacturing.machines.edit')}</h1>
      </div>

      <Card>
        <form className="stack" onSubmit={(e) => void handleSubmit(e)} noValidate>
          {error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {selectField('masterData.fields.company', company, setCompany, companies, true)}
          {selectField('manufacturing.fields.site', site, setSite, sites, false)}
          {selectField('manufacturing.workCenters.title', workCenter, setWorkCenter, workCenters, false)}

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

          <FormField label={t('manufacturing.fields.capabilityProfile')}>
            {({ id: fieldId }) => (
              <textarea
                id={fieldId}
                className="input"
                rows={4}
                value={capabilityProfile}
                onChange={(e) => setCapabilityProfile(e.target.value)}
                disabled={submitting}
                placeholder='{"max_width_mm": 1200}'
              />
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
              onClick={() => navigate(`/manufacturing/machines/${id}`)}
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
