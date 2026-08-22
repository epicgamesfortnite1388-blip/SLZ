import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { apiClient } from '@/api/client';
import { fetchCostSummary, type CostSummaryItem } from '@/api/costing';
import { isApiError } from '@/api/types';
import { Alert, Card, Spinner } from '@/components/ui';
import type { Paginated } from '@/api/inventory';

interface MaterialOption {
  id: string;
  code: string;
  name_fa: string;
}

export function CostSummaryPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canView = hasPermission('costing.layer.view');
  const [items, setItems] = useState<CostSummaryItem[]>([]);
  const [materials, setMaterials] = useState<Record<string, MaterialOption>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canView) return;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [summary, matPage] = await Promise.all([
          fetchCostSummary(),
          apiClient.get<Paginated<MaterialOption>>('/catalog/materials/?page_size=500'),
        ]);
        setItems(summary);
        const map: Record<string, MaterialOption> = {};
        for (const m of matPage.results) {
          map[m.id] = m;
        }
        setMaterials(map);
      } catch (err) {
        setError(isApiError(err) ? err.message : t('common.error'));
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [canView, t]);

  if (!canView) return <></>;

  const label = (id: string): string => {
    const m = materials[id];
    return m ? `${m.code} — ${m.name_fa}` : id;
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('costing.summary.title')}</h1>
        <p className="page-header__subtitle">{t('costing.fields.onHandCost')}</p>
      </div>

      <Card>
        {loading && <Spinner />}
        {error && (
          <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        {!loading && !error && (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('costing.fields.material')}</th>
                  <th className="text-end">{t('costing.fields.waCost')}</th>
                  <th className="text-end">{t('costing.fields.onHandQty')}</th>
                  <th className="text-end">{t('costing.fields.onHandCost')}</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={4}>{t('masterData.empty')}</td>
                  </tr>
                ) : (
                  items.map((item) => (
                    <tr key={item.material_id}>
                      <td>{label(item.material_id)}</td>
                      <td className="text-end">{item.wa_unit_cost}</td>
                      <td className="text-end">{item.on_hand_qty}</td>
                      <td className="text-end">{item.on_hand_cost}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}