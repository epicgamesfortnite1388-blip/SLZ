import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { apiClient } from '@/api/client';
import { isApiError } from '@/api/types';
import { Alert, Card, Spinner } from '@/components/ui';

interface StockBalance {
  material_id: string;
  material_code: string;
  material_name: string;
  warehouse_code: string;
  on_hand: string;
  uom: string;
}

export function StockBalancesPage(): JSX.Element {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canView = hasPermission('catalog.material.view');
  const [balances, setBalances] = useState<StockBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canView) return;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const page = await apiClient.get<{
          results: StockBalance[];
        }>('/inventory/balances/?page_size=250');
        setBalances(page.results);
      } catch (err) {
        setError(isApiError(err) ? err.message : t('common.error'));
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [canView, t]);

  if (!canView) return <></>;
  if (loading) {
    return (
      <Card title={t('inventory.balances.title')}>
        <Spinner />
      </Card>
    );
  }

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t('inventory.balances.title')}</h1>
        <p className="page-header__subtitle">{t('inventory.balances.subtitle')}</p>
      </div>

      <Card>
        {error && (
          <Alert variant="danger" title={t('common.error')} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('masterData.fields.code')}</th>
                <th>{t('masterData.fields.nameFa')}</th>
                <th>{t('inventory.fields.warehouse')}</th>
                <th className="text-end">{t('masterData.fields.quantity')}</th>
                <th>{t('masterData.fields.uom')}</th>
              </tr>
            </thead>
            <tbody>
              {balances.length === 0 ? (
                <tr>
                  <td colSpan={5}>{t('masterData.empty')}</td>
                </tr>
              ) : (
                balances.map((b, i) => (
                  <tr key={`${b.material_id}-${b.warehouse_code}-${i}`}>
                    <td>{b.material_code}</td>
                    <td>{b.material_name}</td>
                    <td>{b.warehouse_code}</td>
                    <td className="text-end">{b.on_hand}</td>
                    <td>{b.uom}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}