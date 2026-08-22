import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { Company } from '@/api/organization';

/**
 * Browse companies — the root of company scoping. Manage access is gated by
 * `organization.company.manage`; the code is unique and enforced server-side.
 */
export function CompaniesPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<Company>('/organization/companies/');

  const columns: Column<Company>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    { headerKey: 'masterData.fields.nameEn', render: (r) => r.name_en || '—' },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <CollectionView
      titleKey="organization.companies.title"
      subtitleKey="organization.companies.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('organization.company.manage') ? (
          <Link to="/organization/companies/new">
            <Button size="sm">{t('organization.companies.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
