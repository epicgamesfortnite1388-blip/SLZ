import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import {
  createCustomerProfile,
  createSupplierProfile,
  fetchCollection,
  fetchCustomerProfile,
  fetchSupplierProfile,
  updateCustomerProfile,
  updateSupplierProfile,
} from '@/api/masterData';
import { isApiError } from '@/api/types';
import { BoolCell } from '@/components/CollectionView';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

/**
 * Customer / supplier 1:1 role-profile panels for the partner detail page.
 * These surface the role-specific commercial attributes that live on the
 * backend role extensions (COA requirement + sales line; supplier approval +
 * evaluation stub). Read follows ``partners.partner.view``; writes require
 * ``partners.partner.manage`` (server-enforced, mirrored here as a read-only
 * view for non-managers).
 */

interface PanelProps {
  partnerId: string;
  /** Whether the partner carries this role at all. */
  enabled: boolean;
}

/** Product-group options for the customer "sales line" picker. */
interface ProductGroupOption {
  id: string;
  code: string;
  name_fa: string;
}

function useRoleProfile<T>(
  fetcher: (partnerId: string) => Promise<T | null>,
  partnerId: string,
  enabled: boolean,
): { profile: T | null; loaded: boolean; error: string | null; reload: () => void } {
  const { t } = useTranslation();
  const [profile, setProfile] = useState<T | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    if (!enabled) {
      setLoaded(true);
      setProfile(null);
      return undefined;
    }
    let active = true;
    setError(null);
    setLoaded(false);
    fetcher(partnerId)
      .then((p) => {
        if (active) {
          setProfile(p);
          setLoaded(true);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(isApiError(err) ? err.message : t('common.error'));
          setLoaded(true);
        }
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetcher, partnerId, enabled, t]);

  useEffect(() => {
    const cleanup = reload();
    return typeof cleanup === 'function' ? cleanup : undefined;
  }, [reload]);

  return { profile, loaded, error, reload };
}

function ReadOnlyFields({ fields }: { fields: DetailField[] }): JSX.Element {
  return <RecordDetail fields={fields} />;
}

/** Shared single-record save bar used by both panels (managers only). */
function SaveBar({
  onSubmit,
  submitting,
  error,
  children,
}: {
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  submitting: boolean;
  error: string | null;
  children?: ReactNode;
}): JSX.Element {
  const { t } = useTranslation();
  return (
    <form className="stack" onSubmit={onSubmit}>
      {error && (
        <Alert variant="danger" title={t('common.error')}>
          <p>{error}</p>
        </Alert>
      )}
      {children}
      <div className="form-actions">
        <Button type="submit" size="sm" loading={submitting}>
          {t('masterData.save')}
        </Button>
      </div>
    </form>
  );
}

export function CustomerProfilePanel({ partnerId, enabled }: PanelProps): JSX.Element | null {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canManage = hasPermission('partners.partner.manage');
  const { profile, loaded, error, reload } = useRoleProfile(
    fetchCustomerProfile,
    partnerId,
    enabled,
  );

  const [salesLine, setSalesLine] = useState('');
  const [tolerance, setTolerance] = useState('');
  const [requiresCoa, setRequiresCoa] = useState(false);
  const [notes, setNotes] = useState('');
  const [groups, setGroups] = useState<ProductGroupOption[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [saveErr, setSaveErr] = useState<string | null>(null);

  // Product-group options load once for the sales-line picker.
  useEffect(() => {
    let cancelled = false;
    fetchCollection<ProductGroupOption>('/catalog/product-groups/', { pageSize: 100 })
      .then((page) => {
        if (!cancelled) setGroups(page.results);
      })
      .catch(() => {
        /* Non-fatal: the picker simply stays empty. */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!profile) return;
    setSalesLine(profile.sales_line ?? '');
    setTolerance(profile.delivery_tolerance_pct ?? '');
    setRequiresCoa(profile.requires_coa);
    setNotes(profile.notes ?? '');
  }, [profile]);

  if (!enabled) return null;

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setSaveErr(null);
    setSubmitting(true);
    try {
      const payload = {
        sales_line: salesLine || null,
        delivery_tolerance_pct: tolerance === '' ? null : tolerance,
        requires_coa: requiresCoa,
        notes,
      };
      if (profile) await updateCustomerProfile(profile.id, payload);
      else await createCustomerProfile({ partner: partnerId, ...payload });
      reload();
    } catch (err) {
      setSaveErr(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const groupLabel =
    groups.find((g) => g.id === (profile?.sales_line ?? ''))?.name_fa ?? profile?.sales_line;

  const readOnly: DetailField[] = [
    {
      labelKey: 'partners.customerProfile.salesLine',
      value: groupLabel ?? '—',
    },
    { labelKey: 'partners.customerProfile.tolerance', value: profile?.delivery_tolerance_pct ?? '—' },
    {
      labelKey: 'partners.customerProfile.requiresCoa',
      value: <BoolCell value={Boolean(profile?.requires_coa)} />,
    },
    { labelKey: 'sales.fields.notes', value: profile?.notes || '—' },
  ];

  return (
    <Card title={t('partners.customerProfile.title')}>
      {!loaded && <Spinner label={t('common.loading')} />}
      {error && <p>{error}</p>}
      {loaded && !error && (
        <>
          {!profile && (
            <Alert variant="info" title={t('partners.customerProfile.missing')}>
              <p>{t('partners.customerProfile.missingHint')}</p>
            </Alert>
          )}
          {!canManage && <ReadOnlyFields fields={readOnly} />}
          {canManage && (
            <SaveBar submitting={submitting} error={saveErr} onSubmit={(e) => void handleSubmit(e)}>
              <FormField label={t('partners.customerProfile.salesLine')}>
                {({ id }) => (
                  <select
                    id={id}
                    className="input"
                    value={salesLine}
                    onChange={(e) => setSalesLine(e.target.value)}
                    disabled={submitting}
                  >
                    <option value="">—</option>
                    {groups.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name_fa} ({g.code})
                      </option>
                    ))}
                  </select>
                )}
              </FormField>
              <FormField label={t('partners.customerProfile.tolerance')}>
                {({ id }) => (
                  <Input
                    id={id}
                    value={tolerance}
                    onChange={(e) => setTolerance(e.target.value)}
                    disabled={submitting}
                  />
                )}
              </FormField>
              <div className="checkbox-row">
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={requiresCoa}
                    onChange={(e) => setRequiresCoa(e.target.checked)}
                    disabled={submitting}
                  />
                  {t('partners.customerProfile.requiresCoa')}
                </label>
              </div>
              <FormField label={t('sales.fields.notes')}>
                {({ id }) => (
                  <Input
                    id={id}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    disabled={submitting}
                  />
                )}
              </FormField>
            </SaveBar>
          )}
        </>
      )}
    </Card>
  );
}

export function SupplierProfilePanel({ partnerId, enabled }: PanelProps): JSX.Element | null {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canManage = hasPermission('partners.partner.manage');
  const { profile, loaded, error, reload } = useRoleProfile(
    fetchSupplierProfile,
    partnerId,
    enabled,
  );

  const [isApproved, setIsApproved] = useState(false);
  const [score, setScore] = useState('');
  const [leadTime, setLeadTime] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [saveErr, setSaveErr] = useState<string | null>(null);

  useEffect(() => {
    if (!profile) return;
    setIsApproved(profile.is_approved);
    setScore(profile.evaluation_score ?? '');
    setLeadTime(profile.lead_time_days === null ? '' : String(profile.lead_time_days));
    setNotes(profile.notes ?? '');
  }, [profile]);

  if (!enabled) return null;

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setSaveErr(null);
    setSubmitting(true);
    try {
      const payload = {
        is_approved: isApproved,
        evaluation_score: score === '' ? null : score,
        lead_time_days: leadTime === '' ? null : Number(leadTime),
        notes,
      };
      if (profile) await updateSupplierProfile(profile.id, payload);
      else await createSupplierProfile({ partner: partnerId, ...payload });
      reload();
    } catch (err) {
      setSaveErr(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const readOnly: DetailField[] = [
    {
      labelKey: 'partners.supplierProfile.isApproved',
      value: <BoolCell value={Boolean(profile?.is_approved)} />,
    },
    {
      labelKey: 'partners.supplierProfile.evaluationScore',
      value: profile?.evaluation_score ?? '—',
    },
    { labelKey: 'partners.supplierProfile.leadTime', value: profile?.lead_time_days ?? '—' },
    { labelKey: 'sales.fields.notes', value: profile?.notes || '—' },
  ];

  return (
    <Card title={t('partners.supplierProfile.title')}>
      {!loaded && <Spinner label={t('common.loading')} />}
      {error && <p>{error}</p>}
      {loaded && !error && (
        <>
          {!profile && (
            <Alert variant="info" title={t('partners.supplierProfile.missing')}>
              <p>{t('partners.supplierProfile.missingHint')}</p>
            </Alert>
          )}
          {!canManage && <ReadOnlyFields fields={readOnly} />}
          {canManage && (
            <SaveBar submitting={submitting} error={saveErr} onSubmit={(e) => void handleSubmit(e)}>
              <div className="checkbox-row">
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={isApproved}
                    onChange={(e) => setIsApproved(e.target.checked)}
                    disabled={submitting}
                  />
                  {t('partners.supplierProfile.isApproved')}
                </label>
              </div>
              <FormField label={t('partners.supplierProfile.evaluationScore')}>
                {({ id }) => (
                  <Input
                    id={id}
                    value={score}
                    onChange={(e) => setScore(e.target.value)}
                    disabled={submitting}
                  />
                )}
              </FormField>
              <FormField label={t('partners.supplierProfile.leadTime')}>
                {({ id }) => (
                  <Input
                    id={id}
                    type="number"
                    min={0}
                    value={leadTime}
                    onChange={(e) => setLeadTime(e.target.value)}
                    disabled={submitting}
                  />
                )}
              </FormField>
              <FormField label={t('sales.fields.notes')}>
                {({ id }) => (
                  <Input
                    id={id}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    disabled={submitting}
                  />
                )}
              </FormField>
            </SaveBar>
          )}
        </>
      )}
    </Card>
  );
}
