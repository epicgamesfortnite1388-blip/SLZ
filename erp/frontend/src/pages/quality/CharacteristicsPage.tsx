import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { QualityCharacteristic } from '@/api/quality';

/**
 * Browse the company quality-characteristic catalogue. The datatype column
 * resolves its label from i18n; the method is free-text data (Q-039 OPEN). The
 * create link shows only to a user with the manage permission.
 */
export function CharacteristicsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<QualityCharacteristic>(
    '/quality/characteristics/',
  );

  const columns: Column<QualityCharacteristic>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    {
      headerKey: 'quality.fields.datatype',
      render: (r) => t(`quality.datatypes.${r.datatype}`),
    },
    { headerKey: 'quality.fields.method', render: (r) => r.method || '—' },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <CollectionView
      titleKey="quality.characteristics.title"
      subtitleKey="quality.characteristics.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('quality.characteristic.manage') ? (
          <Link to="/quality/characteristics/new">
            <Button size="sm">{t('quality.characteristics.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
