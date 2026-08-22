import { useNavigate } from 'react-router-dom';
import { BoolCell, CollectionView, type Column } from '@/components/CollectionView';
import { useCollection } from '@/hooks/useCollection';
import type { Employee } from '@/api/masterData';

const columns: Column<Employee>[] = [
  { headerKey: 'employees.code', render: (r) => r.employee_code },
  {
    headerKey: 'masterData.fields.nameFa',
    render: (r) => `${r.first_name_fa} ${r.last_name_fa}`.trim(),
  },
  { headerKey: 'employees.jobTitle', render: (r) => r.job_title || '—' },
  {
    headerKey: 'masterData.fields.active',
    render: (r) => <BoolCell value={r.is_active} />,
    align: 'center',
  },
];

export function EmployeesPage(): JSX.Element {
  const collection = useCollection<Employee>('/hr/employees/');
  const navigate = useNavigate();
  return (
    <CollectionView
      titleKey="employees.title"
      subtitleKey="employees.subtitle"
      columns={columns}
      rowKey={(r) => r.id}
      collection={collection}
      onRowClick={(row) => navigate(`/master-data/employees/${row.id}`)}
    />
  );
}
