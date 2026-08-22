import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { PlatformPermission } from '@/api/identity';

export function PermissionsPage(): JSX.Element {
  const collection = useCollection<PlatformPermission>('/auth/permissions/');

  const columns: Column<PlatformPermission>[] = [
    { headerKey: 'permissions.fields.code', render: (r) => r.code },
    { headerKey: 'permissions.fields.module', render: (r) => r.module, align: 'center' },
    { headerKey: 'permissions.fields.descriptionEn', render: (r) => r.description_en || '—' },
    { headerKey: 'permissions.fields.descriptionFa', render: (r) => r.description_fa || '—' },
  ];

  return (
    <CollectionView
      titleKey="permissions.title"
      subtitleKey="permissions.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
    />
  );
}