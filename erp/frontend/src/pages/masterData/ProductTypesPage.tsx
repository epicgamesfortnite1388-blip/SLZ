import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { ProductType } from '@/api/masterData';

export function ProductTypesPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<ProductType>('/catalog/product-types/');

  const columns: Column<ProductType>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    { headerKey: 'masterData.fields.nameEn', render: (r) => r.name_en || '—' },
    { headerKey: 'masterData.fields.active', render: (r) => <BoolCell value={r.is_active} />, align: 'center' },
  ];

  return (
    <CollectionView
      titleKey="productTypes.title"
      subtitleKey="productTypes.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('catalog.producttaxonomy.manage') ? (
          <Link to="/master-data/product-types/new">
            <Button size="sm">{t('productTypes.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}