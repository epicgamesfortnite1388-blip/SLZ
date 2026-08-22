import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { WorkflowDefinition } from '@/api/workflow';

/**
 * Browse approval-workflow definitions (engine configuration). Manage access is
 * gated by `workflow.definition.manage`; `code` is unique server-side. The
 * definition only describes the approval *shape* — no business routing rule is
 * encoded here (do-not-build-yet #7).
 */
export function WorkflowDefinitionsPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const collection = useCollection<WorkflowDefinition>('/workflow/definitions/');

  const columns: Column<WorkflowDefinition>[] = [
    { headerKey: 'masterData.fields.code', render: (r) => r.code },
    { headerKey: 'masterData.fields.nameFa', render: (r) => r.name_fa },
    {
      headerKey: 'workflow.definitions.mode',
      render: (r) => t(`workflow.modes.${r.approval_mode}`),
    },
    {
      headerKey: 'masterData.fields.active',
      render: (r) => <BoolCell value={r.is_active} />,
      align: 'center',
    },
  ];

  return (
    <CollectionView
      titleKey="workflow.definitions.title"
      subtitleKey="workflow.definitions.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      headerAction={
        hasPermission('workflow.definition.manage') ? (
          <Link to="/workflow/definitions/new">
            <Button size="sm">{t('workflow.definitions.new')}</Button>
          </Link>
        ) : null
      }
    />
  );
}
