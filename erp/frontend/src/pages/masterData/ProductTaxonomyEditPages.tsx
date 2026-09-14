import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import type {
  Paginated,
  ProductClass,
  ProductFamily,
  ProductGroup,
  ProductType,
} from '@/api/masterData';
import { isApiError } from '@/api/types';
import { Alert, Button, Card, FormField, Input, Spinner } from '@/components/ui';

/** Shared loader + form plumbing for the four taxonomy edit pages. */
function useTaxonomyEdit<T extends { code: string; name_fa: string; name_en: string | null; is_active: boolean }>(
  endpoint: string,
) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id = '' } = useParams();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [code, setCode] = useState('');
  const [nameFa, setNameFa] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<T>(`${endpoint}${id}/`)
      .then((record) => {
        if (cancelled) return;
        setCode(record.code);
        setNameFa(record.name_fa);
        setNameEn(record.name_en ?? '');
        setIsActive(record.is_active);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setLoadError(isApiError(err) ? err.message : t('common.error'));
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [endpoint, id, t]);

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
    extra: Record<string, unknown>,
  ): Promise<void> => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await apiClient.patch<T>(`${endpoint}${id}/`, {
        ...extra,
        name_fa: nameFa,
        name_en: nameEn,
        is_active: isActive,
      });
      navigate(-1);
    } catch (err) {
      setError(isApiError(err) ? err.message : t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  return {
    t,
    navigate,
    loading,
    loadError,
    code,
    nameFa,
    nameEn,
    isActive,
    error,
    submitting,
    setNameFa,
    setNameEn,
    setIsActive,
    setError,
    handleSubmit,
  };
}

function EditShell({
  titleKey,
  state,
  children,
  getExtra,
}: {
  titleKey: string;
  state: ReturnType<typeof useTaxonomyEdit>;
  children?: React.ReactNode;
  /** Optional extra payload fields resolved at submit time (e.g. parent FK). */
  getExtra?: () => Record<string, unknown>;
}): JSX.Element {
  const { t } = state;
  if (state.loading) {
    return (
      <div className="table-state">
        <Spinner label={t('common.loading')} />
      </div>
    );
  }
  if (state.loadError) {
    return (
      <div className="stack">
        <Alert variant="danger" title={t('common.error')}>
          <p>{state.loadError}</p>
          <Button variant="secondary" size="sm" onClick={() => window.history.back()}>
            {t('common.back')}
          </Button>
        </Alert>
      </div>
    );
  }
  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{t(titleKey)}</h1>
      </div>
      <Card>
        <form
          className="stack"
          onSubmit={(e) => {
            e.preventDefault();
            void state.handleSubmit(e, getExtra ? getExtra() : {});
          }}
          noValidate
        >
          {state.error && (
            <Alert variant="danger" title={t('common.error')} onClose={() => state.setError(null)}>
              {state.error}
            </Alert>
          )}
          {children}
          <FormField label={t('masterData.fields.code')}>
            {({ id: fieldId }) => <Input id={fieldId} value={state.code} disabled readOnly />}
          </FormField>
          <FormField label={t('masterData.fields.nameFa')} required>
            {({ id: fieldId }) => (
              <Input
                id={fieldId}
                value={state.nameFa}
                onChange={(e) => state.setNameFa(e.target.value)}
                disabled={state.submitting}
                required
              />
            )}
          </FormField>
          <FormField label={t('masterData.fields.nameEn')}>
            {({ id: fieldId }) => (
              <Input
                id={fieldId}
                value={state.nameEn}
                onChange={(e) => state.setNameEn(e.target.value)}
                disabled={state.submitting}
              />
            )}
          </FormField>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={state.isActive}
              onChange={(e) => state.setIsActive(e.target.checked)}
              disabled={state.submitting}
            />
            {t('masterData.fields.active')}
          </label>
          <div className="form-actions">
            <Button type="submit" loading={state.submitting}>
              {t('masterData.save')}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => window.history.back()}
              disabled={state.submitting}
            >
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

/** Product-group edit (top commercial grouping). */
export function ProductGroupEditPage(): JSX.Element {
  const state = useTaxonomyEdit<ProductGroup>('/catalog/product-groups/');
  return <EditShell titleKey="productGroups.edit" state={state} />;
}

/** Product-type edit (taxonomy level 1, نوع). */
export function ProductTypeEditPage(): JSX.Element {
  const state = useTaxonomyEdit<ProductType>('/catalog/product-types/');
  return <EditShell titleKey="productTypes.edit" state={state} />;
}

/** Product-class edit (taxonomy level 2, طبقه) — parent type is selectable. */
export function ProductClassEditPage(): JSX.Element {
  const { t } = useTranslation();
  const { id = '' } = useParams();
  const state = useTaxonomyEdit<ProductClass>('/catalog/product-classes/');
  const [types, setTypes] = useState<{ id: string; name_fa: string; code: string }[]>([]);
  const [productType, setProductType] = useState('');

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<Paginated<{ id: string; name_fa: string; code: string }>>('/catalog/product-types/?page_size=200')
      .then((res) => {
        if (cancelled) return;
        setTypes(res.results);
      })
      .catch(() => {});
    apiClient
      .get<ProductClass>(`/catalog/product-classes/${id}/`)
      .then((record) => {
        if (cancelled) return;
        setProductType(record.product_type);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [id]);

  return (
    <EditShell titleKey="productClasses.edit" state={state} getExtra={() => ({ product_type: productType || null })}>
      <FormField label={t('productTypes.title')}>
        {({ id: fieldId }) => (
          <select
            id={fieldId}
            className="input"
            value={productType}
            onChange={(e) => setProductType(e.target.value)}
            disabled={state.submitting}
          >
            <option value="">—</option>
            {types.map((tp) => (
              <option key={tp.id} value={tp.id}>
                {tp.name_fa} ({tp.code})
              </option>
            ))}
          </select>
        )}
      </FormField>
    </EditShell>
  );
}

/** Product-family edit — parent class is selectable. */
export function ProductFamilyEditPage(): JSX.Element {
  const { t } = useTranslation();
  const { id = '' } = useParams();
  const state = useTaxonomyEdit<ProductFamily>('/catalog/product-families/');
  const [classes, setClasses] = useState<{ id: string; name_fa: string; code: string }[]>([]);
  const [productClass, setProductClass] = useState('');

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<Paginated<{ id: string; name_fa: string; code: string }>>('/catalog/product-classes/?page_size=200')
      .then((res) => {
        if (cancelled) return;
        setClasses(res.results);
      })
      .catch(() => {});
    apiClient
      .get<ProductFamily>(`/catalog/product-families/${id}/`)
      .then((record) => {
        if (cancelled) return;
        setProductClass(record.product_class);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [id]);

  return (
    <EditShell titleKey="productFamilies.edit" state={state} getExtra={() => ({ product_class: productClass || null })}>
      <FormField label={t('productClasses.title')}>
        {({ id: fieldId }) => (
          <select
            id={fieldId}
            className="input"
            value={productClass}
            onChange={(e) => setProductClass(e.target.value)}
            disabled={state.submitting}
          >
            <option value="">—</option>
            {classes.map((cl) => (
              <option key={cl.id} value={cl.id}>
                {cl.name_fa} ({cl.code})
              </option>
            ))}
          </select>
        )}
      </FormField>
    </EditShell>
  );
}
