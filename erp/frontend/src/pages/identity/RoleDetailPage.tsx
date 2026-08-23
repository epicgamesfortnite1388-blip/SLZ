import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import { fetchPermissions, type PlatformPermission } from '@/api/identity';
import { isApiError } from '@/api/types';
import type { Role } from '@/api/roles';
import { Alert, Button, Card, Spinner } from '@/components/ui';

export function RoleDetailPage(): JSX.Element {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [role, setRole] = useState<Role | null>(null);
  const [allPerms, setAllPerms] = useState<PlatformPermission[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    Promise.all([
      apiClient.get<Role>(`/auth/roles/${id}/`),
      fetchPermissions(),
    ]).then(([r, p]) => {
      if (cancelled) return;
      setRole(r);
      setAllPerms(p.results);
      setSelected(new Set(r.permission_codes));
    }).catch(() => {}).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [id]);

  const toggle = (code: string) => {
    const next = new Set(selected);
    if (next.has(code)) next.delete(code); else next.add(code);
    setSelected(next);
  };

  const grouped = allPerms.reduce<Record<string, PlatformPermission[]>>((acc, p) => {
    const mod = p.module || 'other';
    (acc[mod] ??= []).push(p);
    return acc;
  }, {});

  const handleSave = async () => {
    if (!id) return;
    setError(null);
    setSaving(true);
    try {
      await apiClient.patch(`/auth/roles/${id}/`, { set_permission_codes: [...selected] });
      navigate('/identity/roles');
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="table-state"><Spinner label={t('common.loading')} /></div>;
  if (!role) return <Alert variant="danger" title={t('common.error')}>{t('common.notFound')}</Alert>;

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{role.code}</h1>
        <p className="page-header__subtitle">{role.name_en || role.name_fa}</p>
      </div>

      {error && <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>{error}</Alert>}

      <Card title={t('permissions.title')}>
        <div style={{ maxHeight: '60vh', overflow: 'auto' }}>
          {Object.entries(grouped).map(([mod, perms]) => (
            <details key={mod} open>
              <summary style={{ fontWeight: 600, cursor: 'pointer', padding: '0.5rem 0' }}>{mod}</summary>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, paddingInlineStart: '1rem' }}>
                {perms.map((p) => (
                  <label key={p.code} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', cursor: 'pointer' }}>
                    <input type="checkbox" checked={selected.has(p.code)} onChange={() => toggle(p.code)} />
                    <div>
                      <code style={{ fontSize: '0.8rem' }}>{p.code}</code>
                      <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{p.description_en || p.description_fa}</div>
                    </div>
                  </label>
                ))}
              </div>
            </details>
          ))}
        </div>
      </Card>

      <div className="form-actions">
        <Button onClick={handleSave} loading={saving}>{t('masterData.save')}</Button>
        <Button variant="secondary" onClick={() => navigate('/identity/roles')} disabled={saving}>{t('common.cancel')}</Button>
      </div>
    </div>
  );
}