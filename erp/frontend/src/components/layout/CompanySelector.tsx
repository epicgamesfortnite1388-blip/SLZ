import { useTranslation } from 'react-i18next';
import { useAuth } from '@/auth/AuthContext';
import { apiClient } from '@/api/client';
import { useEffect, useState } from 'react';

interface CompanyOption {
  id: string;
  code: string;
  name_en: string;
  name_fa: string;
}

/** Company selector: dropdown in the header that switches the active
 *  company context (Q-055). Sends X-SLZ-Company header on all subsequent
 *  API requests and gates permission checks per-company. */
export function CompanySelector(): JSX.Element | null {
  const { t, i18n } = useTranslation();
  const { user, activeCompanyId, setActiveCompany } = useAuth();
  const [companies, setCompanies] = useState<CompanyOption[]>([]);

  useEffect(() => {
    if (!user || user.companies.length === 0) return;
    let cancelled = false;
    apiClient
      .get<{ results: CompanyOption[] }>('/organization/companies/?page_size=100')
      .then((page) => {
        if (cancelled) return;
        const memberIds = new Set(user.companies);
        setCompanies(page.results.filter((c) => memberIds.has(c.id)));
      })
      .catch(() => {
        // Silently ignore — companies just won't show names.
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  if (!user || user.companies.length === 0) return null;

  const isFa = i18n.language === 'fa';
  const companyName = (c: CompanyOption): string =>
    isFa ? c.name_fa || c.code : c.name_en || c.code;

  return (
    <div className="company-selector">
      <select
        className="company-selector__select"
        value={activeCompanyId ?? ''}
        onChange={(e) => {
          setActiveCompany(e.target.value || null);
        }}
        aria-label={t('companySelector.label', 'Select company')}
      >
        <option value="">{t('companySelector.all', 'All companies')}</option>
        {companies.map((c) => (
          <option key={c.id} value={c.id}>
            {companyName(c)}
          </option>
        ))}
      </select>
    </div>
  );
}