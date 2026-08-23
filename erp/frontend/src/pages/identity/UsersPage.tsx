import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import { Button } from '@/components/ui';
import type { PlatformUser } from '@/api/identity';
import { useTranslation } from 'react-i18next';

export function UsersPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const navigate = useNavigate();
  const collection = useCollection<PlatformUser>('/auth/users/');

  const columns: Column<PlatformUser>[] = [
    {
      headerKey: 'users.fields.email',
      render: (r) => (
        <Link to={`/identity/users/${r.id}/edit`} className="link-inline">
          {r.email}
        </Link>
      ),
    },
    { headerKey: 'users.fields.fullName', render: (r) => r.full_name || '—' },
    { headerKey: 'users.fields.language', render: (r) => r.language, align: 'center' },
    { headerKey: 'users.fields.roles', render: (r) => r.roles.join(', ') || '—' },
    { headerKey: 'users.fields.companies', render: (r) => (Array.isArray(r.companies) ? r.companies.length : 0), align: 'center' },
    { headerKey: 'users.fields.isActive', render: (r) => <BoolCell value={r.is_active} />, align: 'center' },
    {
      headerKey: 'masterData.actions',
      render: (r) => (
        <Button size="sm" variant="ghost" onClick={() => navigate(`/identity/users/${r.id}/edit`)}>
          {t('masterData.edit')}
        </Button>
      ),
      align: 'center',
    },
  ];

  const createButton = hasPermission('identity.user.manage') ? (
    <Link to="/identity/users/new">
      <Button size="sm">{t('users.new')}</Button>
    </Link>
  ) : undefined;

  return (
    <CollectionView
      titleKey="users.title"
      subtitleKey="users.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={createButton}
    />
  );
}