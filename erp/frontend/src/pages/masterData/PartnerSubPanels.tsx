import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { isApiError } from '@/api/types';
import {
  createPartnerAddress,
  createPartnerContact,
  fetchPartnerAddresses,
  fetchPartnerContacts,
  type PartnerAddress,
  type PartnerContact,
} from '@/api/masterData';
import { Alert, Button, Card, Input, Spinner } from '@/components/ui';

const CONTACT_KINDS = ['GENERAL', 'SALES', 'TECHNICAL', 'FINANCE', 'LOGISTICS'] as const;
const ADDRESS_KINDS = ['BILLING', 'SHIPPING', 'OTHER'] as const;

interface PanelProps {
  partnerId: string;
}

function usePartnerSubList<T>(
  fetcher: (id: string) => Promise<T[]>,
  partnerId: string,
): { rows: T[] | null; error: string | null; reload: () => void } {
  const { t } = useTranslation();
  const [rows, setRows] = useState<T[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    let active = true;
    setError(null);
    fetcher(partnerId)
      .then((r) => {
        if (active) setRows(r);
      })
      .catch((err: unknown) => {
        if (active) {
          setRows([]);
          setError(isApiError(err) ? err.message : t('common.error'));
        }
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [partnerId, t]);

  useEffect(() => reload(), [reload]);
  return { rows, error, reload };
}

/** Shared compact add-row form used by both panels. */
function AddRowForm({
  canManage,
  submitting,
  error,
  onSubmit,
  children,
}: {
  canManage: boolean;
  submitting: boolean;
  error: string | null;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  children: ReactNode;
}): JSX.Element {
  const { t } = useTranslation();
  if (!canManage) return <></>;
  return (
    <form className="checkbox-row" onSubmit={onSubmit}>
      {error && (
        <Alert variant="danger" title={t('common.error')}>
          <p>{error}</p>
        </Alert>
      )}
      {children}
      <Button type="submit" size="sm" loading={submitting}>
        {t('masterData.save')}
      </Button>
    </form>
  );
}

/** Contacts of one partner: read requires ``partners.contact.view``; adding
 * requires ``partners.contact.manage`` (server-enforced; mirrored in the UI). */
export function PartnerContactsPanel({ partnerId }: PanelProps): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canManage = hasPermission('partners.contact.manage');
  const { rows, error, reload } = usePartnerSubList(fetchPartnerContacts, partnerId);

  const [name, setName] = useState('');
  const [kind, setKind] = useState<string>('GENERAL');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [addErr, setAddErr] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setAddErr(null);
    setSubmitting(true);
    try {
      await createPartnerContact({ partner: partnerId, name, kind, email, phone });
      setName('');
      setEmail('');
      setPhone('');
      reload();
    } catch (err) {
      setAddErr(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card title={t('partners.contacts.title')}>
      {error && <p>{error}</p>}
      {!error && rows === null && <Spinner label={t('common.loading')} />}
      {!error && rows !== null && rows.length === 0 && <p>{t('masterData.empty')}</p>}
      {!error && rows !== null && rows.length > 0 && (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('partners.contacts.name')}</th>
                <th>{t('partners.contacts.kind')}</th>
                <th>{t('partners.contacts.email')}</th>
                <th>{t('partners.contacts.phone')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c: PartnerContact) => (
                <tr key={c.id}>
                  <td>{c.name}{c.is_primary ? ' ★' : ''}</td>
                  <td>{t(`partners.kinds.${c.kind}`)}</td>
                  <td>{c.email || '—'}</td>
                  <td>{c.phone || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <AddRowForm
        canManage={canManage}
        submitting={submitting}
        error={addErr}
        onSubmit={(e) => {
          void handleSubmit(e);
        }}
      >
        <Input
          placeholder={t('partners.contacts.name')}
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          disabled={submitting}
        />
        <select className="input" value={kind} onChange={(e) => setKind(e.target.value)} disabled={submitting}>
          {CONTACT_KINDS.map((k) => (
            <option key={k} value={k}>
              {t(`partners.kinds.${k}`)}
            </option>
          ))}
        </select>
        <Input
          placeholder={t('partners.contacts.email')}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={submitting}
        />
        <Input
          placeholder={t('partners.contacts.phone')}
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          disabled={submitting}
        />
      </AddRowForm>
    </Card>
  );
}

/** Addresses of one partner: same permission model as contacts. */
export function PartnerAddressesPanel({ partnerId }: PanelProps): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canManage = hasPermission('partners.address.manage');
  const { rows, error, reload } = usePartnerSubList(fetchPartnerAddresses, partnerId);

  const [kind, setKind] = useState<string>('SHIPPING');
  const [line1, setLine1] = useState('');
  const [city, setCity] = useState('');
  const [country, setCountry] = useState('');
  const [addErr, setAddErr] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setAddErr(null);
    setSubmitting(true);
    try {
      await createPartnerAddress({ partner: partnerId, kind, line1, city, country });
      setLine1('');
      setCity('');
      reload();
    } catch (err) {
      setAddErr(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card title={t('partners.addresses.title')}>
      {error && <p>{error}</p>}
      {!error && rows === null && <Spinner label={t('common.loading')} />}
      {!error && rows !== null && rows.length === 0 && <p>{t('masterData.empty')}</p>}
      {!error && rows !== null && rows.length > 0 && (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('partners.addresses.kind')}</th>
                <th>{t('partners.addresses.line1')}</th>
                <th>{t('partners.addresses.city')}</th>
                <th>{t('partners.addresses.country')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a: PartnerAddress) => (
                <tr key={a.id}>
                  <td>{t(`partners.kinds.${a.kind}`, { defaultValue: a.kind })}{a.is_primary ? ' ★' : ''}</td>
                  <td>{a.line1}</td>
                  <td>{a.city || '—'}</td>
                  <td>{a.country || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <AddRowForm
        canManage={canManage}
        submitting={submitting}
        error={addErr}
        onSubmit={(e) => {
          void handleSubmit(e);
        }}
      >
        <select className="input" value={kind} onChange={(e) => setKind(e.target.value)} disabled={submitting}>
          {ADDRESS_KINDS.map((k) => (
            <option key={k} value={k}>
              {t(`partners.kinds.${k}`)}
            </option>
          ))}
        </select>
        <Input
          placeholder={t('partners.addresses.line1')}
          value={line1}
          onChange={(e) => setLine1(e.target.value)}
          required
          disabled={submitting}
        />
        <Input
          placeholder={t('partners.addresses.city')}
          value={city}
          onChange={(e) => setCity(e.target.value)}
          disabled={submitting}
        />
        <Input
          placeholder={t('partners.addresses.country')}
          value={country}
          onChange={(e) => setCountry(e.target.value)}
          disabled={submitting}
        />
      </AddRowForm>
    </Card>
  );
}
