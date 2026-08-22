import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { CustomerProduct } from '@/api/engineering';

const columns: Column<CustomerProduct>[] = [
  { headerKey: 'masterData.fields.code', render: (r) => r.code },
  { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
  { headerKey: 'masterData.fields.nameEn', render: (r) => r.name_en || '—' },
  {
    headerKey: 'masterData.fields.active',
    render: (r) => <BoolCell value={r.is_active} />,
    align: 'center',
  },
];

/** Browse customer products (versioned specification roots). */
export function CustomerProductsPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<CustomerProduct>('/engineering/customer-products/');

  return (
    <CollectionView
      titleKey="engineering.customerProducts.title"
      subtitleKey="engineering.customerProducts.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      onRowClick={(r) => navigate(`/engineering/customer-products/${r.id}`)}
      headerAction={
        hasPermission('engineering.customerproduct.manage') ? (
          <Link to="/engineering/customer-products/new">
            <Button size="sm">{t('engineering.customerProducts.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
