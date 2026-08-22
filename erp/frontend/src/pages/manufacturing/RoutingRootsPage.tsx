import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { Routing } from '@/api/manufacturing';

/**
 * Browse routing roots — the durable identity of a versioned routing, each
 * bound to a specific specification revision. The ordered operations live in the
 * immutable revisions; this page lets you browse and create roots.
 */
export function RoutingRootsPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<Routing>('/manufacturing/routings/');
  const canManage = hasPermission('manufacturing.routing.manage');

  const columns: Column<Routing>[] = [
    { headerKey: 'manufacturing.fields.specRevision', render: (r) => r.spec_revision },
    {
      headerKey: 'manufacturing.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <CollectionView
      titleKey="manufacturing.routingRoots.title"
      subtitleKey="manufacturing.routingRoots.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      onRowClick={(r) => navigate(`/manufacturing/routings/${r.id}/revisions`)}
      headerAction={
        canManage ? (
          <Link to="/manufacturing/routings/new">
            <Button size="sm">{t('manufacturing.routingRoots.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}