import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { Site } from '@/api/organization';

/**
 * Browse sites (physical facilities belonging to a company). Manage access is
 * gated by `organization.site.manage`; `code` is unique per company server-side.
 */
export function SitesPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<Site>('/organization/sites/');

  const columns: Column<Site>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    { headerKey: 'organization.fields.timezone', render: (r) => r.timezone || '—' },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <CollectionView
      titleKey="organization.sites.title"
      subtitleKey="organization.sites.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('organization.site.manage') ? (
          <Link to="/organization/sites/new">
            <Button size="sm">{t('organization.sites.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
