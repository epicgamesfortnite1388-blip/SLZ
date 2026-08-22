import { useTranslation } from 'react-i18next';
import { Spinner } from './ui/Spinner';

export interface LoadingScreenProps {
  message?: string;
}

/** Full-viewport loading state used while restoring the session, etc. */
export function LoadingScreen({ message }: LoadingScreenProps): JSX.Element {
  const { t } = useTranslation();
  return (
    <div className="center-screen">
      <Spinner size="lg" label={message ?? t('common.loading')} />
    </div>
  );
}
