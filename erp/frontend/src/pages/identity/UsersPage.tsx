import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { PlatformUser } from '@/api/identity';

export function UsersPage(): JSX.Element {
  const collection = useCollection<PlatformUser>('/auth/users/');

  const columns: Column<PlatformUser>[] = [
    { headerKey: 'users.fields.email', render: (r) => r.email },
    { headerKey: 'users.fields.fullName', render: (r) => r.full_name || '—' },
    { headerKey: 'users.fields.language', render: (r) => r.language, align: 'center' },
    { headerKey: 'users.fields.roles', render: (r) => r.roles.join(', ') || '—' },
    {
      headerKey: 'users.fields.isActive',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <CollectionView
      titleKey="users.title"
      subtitleKey="users.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
    />
  );
}