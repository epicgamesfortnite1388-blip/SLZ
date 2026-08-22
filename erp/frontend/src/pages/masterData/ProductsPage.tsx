import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { Product } from '@/api/masterData';

const columns: Column<Product>[] = [
  { headerKey: 'masterData.fields.code', render: (r) => r.code || '—' },
  { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
  { headerKey: 'masterData.fields.nameEn', render: (r) => r.name_en || '—' },
  {
    headerKey: 'masterData.fields.active',
    render: (r) => <BoolCell value={r.is_active} />,
    align: 'center',
  },
];

export function ProductsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<Product>('/catalog/products/');
  const navigate = useNavigate();
  return (
    <CollectionView
      titleKey="products.title"
      subtitleKey="products.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      onRowClick={(row) => navigate(`/master-data/products/${row.id}`)}
      headerAction={
        hasPermission('catalog.product.manage') ? (
          <Link to="/master-data/products/new">
            <Button size="sm">{t('products.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
