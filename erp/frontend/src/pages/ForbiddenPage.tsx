import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui';

/** 403 view shown when the user lacks a required permission. */
export function ForbiddenPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  return (
    <div className="center-screen">
      <div className="status-page">
        <div className="status-page__code">403</div>
        <h1 className="status-page__title">{t('errors.forbiddenTitle')}</h1>
        <p className="status-page__body">{t('errors.forbiddenBody')}</p>
        <Button variant="primary" onClick={() => navigate('/')}>
          {t('errors.backHome')}
        </Button>
      </div>
    </div>
  );
}
