import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { ProductGroup } from '@/api/masterData';

export function ProductGroupsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<ProductGroup>('/catalog/product-groups/');

  const columns: Column<ProductGroup>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    { headerKey: 'masterData.fields.nameEn', render: (r) => r.name_en || '—' },
    { headerKey: 'masterData.fields.active', render: (r) => <BoolCell value={r.is_active} />, align: 'center' },
  ];

  return (
    <CollectionView
      titleKey="productGroups.title"
      subtitleKey="productGroups.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('catalog.productgroup.manage') ? (
          <Link to="/master-data/product-groups/new">
            <Button size="sm">{t('productGroups.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}