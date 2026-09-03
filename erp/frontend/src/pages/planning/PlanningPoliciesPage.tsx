import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { apiClient } from '@/api/client';
import type { Paginated } from '@/api/masterData';
import type { PlanningPolicy } from '@/api/planning';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';

interface IdName {
  id: string;
  code: string;
  name_fa: string;
}

/**
 * Browse reorder policies for the active company. Each policy pins min/max
 * replenishment parameters for one purchased material or one manufactured
 * product in one warehouse. The engine that consumes them stays read-only and
 * is reached from the "Run planning" action.
 */
export function PlanningPoliciesPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<PlanningPolicy>('/planning/policies/');
  const [warehouses, setWarehouses] = useState<Map<string, string>>(new Map());

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<Paginated<IdName>>('/inventory/warehouses/?page_size=200')
      .then((res) => {
        if (cancelled) return;
        const map = new Map<string, string>();
        res.results.forEach((w) => map.set(w.id, w.name_fa || w.code));
        setWarehouses(map);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const columns: Column<PlanningPolicy>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.item_code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.item_name_fa },
    {
      headerKey: 'planning.fields.itemType',
      render: (r) => t(`planning.itemTypes.${r.item_type}`),
    },
    {
      headerKey: 'planning.fields.warehouse',
      render: (r) => warehouses.get(r.warehouse) ?? r.warehouse,
    },
    { headerKey: 'planning.fields.reorderPoint', render: (r) => r.reorder_point },
    { headerKey: 'planning.fields.targetLevel', render: (r) => r.target_level },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  const canRun = hasPermission('planning.suggestion.view');
  const canManage = hasPermission('planning.policy.manage');

  return (
    <CollectionView
      titleKey="planning.policies.title"
      subtitleKey="planning.policies.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        <div className="table-toolbar__actions">
          {canRun && (
            <Link to="/planning/run">
              <Button size="sm" variant="secondary">
                {t('planning.run.title')}
              </Button>
            </Link>
          )}
          {canManage && (
            <Link to="/planning/policies/new">
              <Button size="sm">{t('planning.policies.new')}</Button>
            </Link>
          )}
        </div>
      }
    />
  );
}
