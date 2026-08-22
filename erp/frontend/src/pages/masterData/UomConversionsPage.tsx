import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { UomConversion } from '@/api/masterData';

export function UomConversionsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<UomConversion>('/catalog/uom-conversions/');

  const columns: Column<UomConversion>[] = [
    { headerKey: 'uoms.fromUom', render: (r) => r.from_uom },
    { headerKey: 'uoms.toUom', render: (r) => r.to_uom },
    { headerKey: 'uoms.factor', render: (r) => r.factor, align: 'end' },
  ];

  return (
    <CollectionView
      titleKey="uomConversions.title"
      subtitleKey="uomConversions.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('catalog.uom.manage') ? (
          <Link to="/master-data/uom-conversions/new">
            <Button size="sm">{t('uomConversions.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}