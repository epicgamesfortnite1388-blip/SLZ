import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { ProductFamily } from '@/api/masterData';

export function ProductFamiliesPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<ProductFamily>('/catalog/product-families/');

  const columns: Column<ProductFamily>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    { headerKey: 'masterData.fields.nameEn', render: (r) => r.name_en || '—' },
    { headerKey: 'masterData.fields.active', render: (r) => <BoolCell value={r.is_active} />, align: 'center' },
  ];

  return (
    <CollectionView
      titleKey="productFamilies.title"
      subtitleKey="productFamilies.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('catalog.producttaxonomy.manage') ? (
          <Link to="/master-data/product-families/new">
            <Button size="sm">{t('productFamilies.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}