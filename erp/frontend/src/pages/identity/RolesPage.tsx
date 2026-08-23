import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import { Button } from '@/components/ui';
import type { Role } from '@/api/roles';

/** Browse platform roles with detail and create actions. */
export function RolesPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const collection = useCollection<Role>('/auth/roles/');

  const columns: Column<Role>[] = [
    {
      headerKey: 'masterData.fields.code',
      render: (r) => (
        <Link to={`/identity/roles/${r.id}`} className="link-inline">
          {r.code}
        </Link>
      ),
    },
    { headerKey: 'roles.fields.nameEn', render: (r) => r.name_en || '—' },
    { headerKey: 'roles.fields.nameFa', render: (r) => r.name_fa || '—' },
    { headerKey: 'roles.fields.permissions', align: 'center', render: (r) => r.permission_codes.length },
    { headerKey: 'roles.fields.isSystem', align: 'center', render: (r) => <BoolCell value={r.is_system} /> },
    {
      headerKey: 'masterData.actions',
      align: 'center',
      render: (r) => (
        <Button size="sm" variant="ghost" onClick={() => navigate(`/identity/roles/${r.id}`)}>
          {t('permissions.title')}
        </Button>
      ),
    },
  ];

  const createButton = (
    <Link to="/identity/roles/new">
      <Button size="sm">{t('roles.new')}</Button>
    </Link>
  );

  return (
    <CollectionView
      titleKey="roles.title"
      subtitleKey="roles.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={createButton}
    />
  );
}