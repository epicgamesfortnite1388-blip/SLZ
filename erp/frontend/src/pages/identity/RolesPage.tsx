import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { Role } from '@/api/roles';

/**
 * Browse platform roles. Read-oriented: permission assignment happens through
 * the API/seed tooling for now; this page makes the catalogue visible to
 * holders of ``identity.role.manage`` (which is also the read gate).
 */
export function RolesPage(): JSX.Element {
  const collection = useCollection<Role>('/auth/roles/');

  const columns: Column<Role>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'roles.fields.nameEn', render: (r) => r.name_en || '—' },
    { headerKey: 'roles.fields.nameFa', render: (r) => r.name_fa || '—' },
    {
      headerKey: 'roles.fields.permissions',
      align: 'center',
      render: (r) => r.permission_codes.length,
    },
    {
      headerKey: 'roles.fields.isSystem',
      align: 'center',
      render: (r) => <BoolCell value={r.is_system} />,
    },
  ];

  return (
    <CollectionView
      titleKey="roles.title"
      subtitleKey="roles.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
    />
  );
}
