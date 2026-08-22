import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { ProductClass } from '@/api/masterData';

export function ProductClassesPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<ProductClass>('/catalog/product-classes/');

  const columns: Column<ProductClass>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    { headerKey: 'masterData.fields.nameEn', render: (r) => r.name_en || '—' },
    { headerKey: 'masterData.fields.active', render: (r) => <BoolCell value={r.is_active} />, align: 'center' },
  ];

  return (
    <CollectionView
      titleKey="productClasses.title"
      subtitleKey="productClasses.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('catalog.producttaxonomy.manage') ? (
          <Link to="/master-data/product-classes/new">
            <Button size="sm">{t('productClasses.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}