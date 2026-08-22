import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { Partner } from '@/api/masterData';

export function PartnersPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<Partner>('/partners/partners/');

  const columns: Column<Partner>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    { headerKey: 'masterData.fields.nameEn', render: (r) => r.name_en || '—' },
    {
      headerKey: 'partners.roles',
      render: (r) => {
        const roles: string[] = [];
        if (r.is_customer) roles.push('C');
        if (r.is_supplier) roles.push('S');
        return roles.join(' / ') || '—';
      },
    },
    {
      headerKey: 'partners.sanctioned',
      render: (r) => <BoolCell value={r.is_sanctioned} />,
      align: 'center',
    },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
    {
      headerKey: 'common.actions',
      align: 'end',
      render: (r) => (
        <Link to={`/master-data/partners/${r.id}`} className="link-inline">
          {t('common.view')}
        </Link>
      ),
    },
  ];

  return (
    <CollectionView
      titleKey="partners.title"
      subtitleKey="partners.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('partners.partner.manage') ? (
          <Link to="/master-data/partners/new">
            <Button size="sm">{t('partners.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
