import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { BillOfMaterials } from '@/api/manufacturing';

/**
 * Browse BOM roots — the durable identity of a versioned bill of materials,
 * each bound to a specific specification revision. The real material structure
 * lives in the immutable revisions; this page lets you browse and create roots.
 */
export function BomRootsPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const collection = useCollection<BillOfMaterials>('/manufacturing/boms/');
  const canManage = hasPermission('manufacturing.bom.manage');

  const columns: Column<BillOfMaterials>[] = [
    { headerKey: 'manufacturing.fields.specRevision', render: (r) => r.spec_revision },
    {
      headerKey: 'manufacturing.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <CollectionView
      titleKey="manufacturing.bomRoots.title"
      subtitleKey="manufacturing.bomRoots.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      onRowClick={(r) => navigate(`/manufacturing/boms/${r.id}/revisions`)}
      headerAction={
        canManage ? (
          <Link to="/manufacturing/boms/new">
            <Button size="sm">{t('manufacturing.bomRoots.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}