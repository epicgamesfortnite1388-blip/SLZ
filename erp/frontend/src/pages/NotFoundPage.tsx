import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui';

/** 404 view. */
export function NotFoundPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  return (
    <div className="center-screen">
      <div className="status-page">
        <div className="status-page__code">404</div>
        <h1 className="status-page__title">{t('errors.notFoundTitle')}</h1>
        <p className="status-page__body">{t('errors.notFoundBody')}</p>
        <Button variant="primary" onClick={() => navigate('/')}>
          {t('errors.backHome')}
        </Button>
      </div>
    </div>
  );
}
