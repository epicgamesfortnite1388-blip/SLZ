import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import {
  fetchCustomerProduct,
  listSpecColors,
  listSpecLayers,
  listSpecParameters,
  listSpecificationRevisions,
  type CustomerProduct,
  type SpecColor,
  type SpecLayer,
  type SpecParameter,
  type SpecificationRevision,
} from '@/api/engineering';
import {
  fetchMaterial,
  fetchPartner,
  fetchProductFamily,
  fetchProductGroup,
  fetchUom,
} from '@/api/masterData';
import { isApiError } from '@/api/types';
import { formatDateTime } from '@/i18n/dates';
import { AttachmentPanel } from '@/components/AttachmentPanel';
import { AuditHistoryPanel } from '@/components/AuditHistoryPanel';
import { RecordDetail, type DetailField } from '@/components/RecordDetail';
import { Alert, Button, Card, Spinner } from '@/components/ui';
import { useAuth } from '@/auth/AuthContext';


/**
 * Detail of one customer product: identity header, the full specification
 * revision chain (draft → active → superseded, immutable once active), and the
 * selected revision's structure/print/parameter tables plus audit history.
 * All data comes from existing `engineering.*.view`-gated endpoints; the
 * lifecycle itself stays server-authoritative.
 */
export function CustomerProductDetailPage(): JSX.Element {
  const { t, i18n } = useTranslation();
  const { hasPermission } = useAuth();

  /** Locale-aware timestamp rendering (Jalali for fa). */
  const when = (iso: string | null): string => formatDateTime(iso, i18n.language);
  const { id = '' } = useParams();
  const [product, setProduct] = useState<CustomerProduct | null>(null);
  const [revisions, setRevisions] = useState<SpecificationRevision[] | null>(null);
  const [selected, setSelected] = useState<SpecificationRevision | null>(null);
  const [layers, setLayers] = useState<SpecLayer[]>([]);
  const [colors, setColors] = useState<SpecColor[]>([]);
  const [params, setParams] = useState<SpecParameter[]>([]);
  const [referenceLabels, setReferenceLabels] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  // Load the root record + its whole revision chain once.
  useEffect(() => {
    let active = true;
    setError(null);
    Promise.all([fetchCustomerProduct(id), listSpecificationRevisions(id)])
      .then(([p, revs]) => {
        if (!active) return;
        setProduct(p);
        setRevisions(revs);
        // Preselect the ACTIVE revision, else the newest.
        setSelected(revs.find((r) => r.status === 'ACTIVE') ?? revs[0] ?? null);
      })
      .catch((err: unknown) => {
        if (active) setError(isApiError(err) ? err.message : t('common.error'));
      });
    return () => {
      active = false;
    };
  }, [id, t]);

  // Resolve existing FK ids so the sample structure can be read without UUID knowledge.
  useEffect(() => {
    if (!product) return;
    let active = true;
    const groupRequest = product.product_group
      ? fetchProductGroup(product.product_group)
      : Promise.resolve(null);
    const familyRequest = product.family
      ? fetchProductFamily(product.family)
      : Promise.resolve(null);
    Promise.all([
      fetchPartner(product.customer),
      fetchUom(product.base_uom),
      groupRequest,
      familyRequest,
    ])
      .then(([customer, uom, group, family]) => {
        if (!active) return;
        setReferenceLabels((current) => ({
          ...current,
          [customer.id]: customer.name_fa || customer.name_en || customer.code,
          [uom.id]: uom.name_fa || uom.name_en || uom.code,
          ...(group ? { [group.id]: group.name_fa || group.name_en || group.code } : {}),
          ...(family ? { [family.id]: family.name_fa || family.name_en || family.code } : {}),
        }));
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [product]);

  // Resolve layer/color material ids for the selected revision.
  useEffect(() => {
    const ids = [...new Set([
      ...layers.map((layer) => layer.material),
      ...colors.flatMap((color) => [color.ink, color.alternative_ink]),
    ].filter((value): value is string => Boolean(value)))];
    if (ids.length === 0) return;
    let active = true;
    Promise.all(ids.map((materialId) => fetchMaterial(materialId)))
      .then((materials) => {
        if (!active) return;
        setReferenceLabels((current) => ({
          ...current,
          ...Object.fromEntries(
            materials.map((material) => [
              material.id,
              material.name_fa || material.name_en || material.code,
            ]),
          ),
        }));
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [layers, colors]);

  const labelFor = (id: string | null): string =>
    id ? referenceLabels[id] ?? id : '—';

  const formatTolerance = (low: string | null, high: string | null): string => {
    if (low == null && high == null) return '—';
    return `${low ?? '…'} / ${high ?? '…'}`;
  };

  const formatParameterValue = (parameter: SpecParameter): string => {
    if (parameter.datatype === 'BOOL') return parameter.value_bool == null ? '—' : String(parameter.value_bool);
    if (parameter.datatype === 'NUMBER') return parameter.value_number ?? '—';
    return parameter.value_text || '—';
  };

  // Load the selected revision's child collections.
  useEffect(() => {
    if (!selected) return;
    let active = true;
    setLayers([]);
    setColors([]);
    setParams([]);
    Promise.all([
      listSpecLayers(selected.id),
      listSpecColors(selected.id),
      listSpecParameters(selected.id),
    ])
      .then(([ls, cs, ps]) => {
        if (!active) return;
        setLayers(ls);
        setColors(cs);
        setParams(ps);
      })
      .catch((err: unknown) => {
        if (active) setError(isApiError(err) ? err.message : t('common.error'));
      });
    return () => {
      active = false;
    };
  }, [selected, t]);

  if (error) {
    return (
      <div className="stack">
        <Alert variant="danger" title={t('common.error')}>
          <p>{error}</p>
          <Button variant="secondary" size="sm" onClick={() => window.history.back()}>
            {t('common.back')}
          </Button>
        </Alert>
      </div>
    );
  }

  if (!product || !revisions) {
    return (
      <div className="table-state">
        <Spinner label={t('common.loading')} />
      </div>
    );
  }

  const headerFields: DetailField[] = [
    { labelKey: 'engineering.fields.code', value: product.code },
    { labelKey: 'engineering.fields.nameFa', value: product.name_fa },
    { labelKey: 'engineering.fields.nameEn', value: product.name_en },
    { labelKey: 'engineering.fields.customer', value: labelFor(product.customer) },
    { labelKey: 'engineering.fields.productGroup', value: labelFor(product.product_group) },
    { labelKey: 'engineering.fields.family', value: labelFor(product.family) },
    { labelKey: 'engineering.fields.baseUom', value: labelFor(product.base_uom) },
    {
      labelKey: 'engineering.fields.isActive',
      value: t(product.is_active ? 'common.yes' : 'common.no'),
    },
  ];

  const specFields: DetailField[] | null = selected
    ? [
        { labelKey: 'engineering.fields.revisionNumber', value: selected.revision_number },
        { labelKey: 'engineering.fields.status', value: t(`engineering.statuses.${selected.status}`) },
        { labelKey: 'engineering.fields.effectiveFrom', value: when(selected.effective_from) },
        { labelKey: 'engineering.fields.effectiveTo', value: when(selected.effective_to) },
        { labelKey: 'engineering.fields.changeReason', value: selected.change_reason || '—' },
        { labelKey: 'engineering.fields.specFormat', value: selected.spec_format },
        { labelKey: 'engineering.fields.bagType', value: selected.bag_type || '—' },
        {
          labelKey: 'engineering.fields.width',
          value:
            selected.width_mm == null
              ? '—'
              : `${selected.width_mm} (${formatTolerance(selected.width_tol_low, selected.width_tol_high)})`,
        },
        {
          labelKey: 'engineering.fields.length',
          value:
            selected.length_mm == null
              ? '—'
              : `${selected.length_mm} (${formatTolerance(selected.length_tol_low, selected.length_tol_high)})`,
        },
        { labelKey: 'engineering.fields.gusset', value: selected.gusset_mm ?? '—' },
        { labelKey: 'engineering.fields.printProcess', value: selected.print_process },
        { labelKey: 'engineering.fields.colors', value: selected.number_of_colors },
        {
          labelKey: 'engineering.fields.lamination',
          value: t(selected.has_lamination ? 'common.yes' : 'common.no'),
        },
        {
          labelKey: 'engineering.fields.coldSeal',
          value: t(selected.has_cold_seal ? 'common.yes' : 'common.no'),
        },
        { labelKey: 'engineering.fields.surfaceFinish', value: selected.surface_finish || '—' },
      ]
    : null;

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-header__title">{product.code}</h1>
        <p className="page-header__subtitle">{product.name_fa}</p>
      </div>

      <RecordDetail title={t('engineering.detail.headerTitle')} fields={headerFields} />

      <Card title={t('engineering.detail.revisionsTitle')}>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('engineering.fields.revisionNumber')}</th>
                <th>{t('engineering.fields.status')}</th>
                <th>{t('engineering.fields.effectiveFrom')}</th>
                <th>{t('engineering.fields.effectiveTo')}</th>
                <th>{t('engineering.fields.changeReason')}</th>
              </tr>
            </thead>
            <tbody>
              {revisions.map((rev) => (
                <tr
                  key={rev.id}
                  onClick={() => setSelected(rev)}
                  className={selected?.id === rev.id ? 'diff-table__row--changed' : undefined}
                >
                  <td>{rev.revision_number}</td>
                  <td>{t(`engineering.statuses.${rev.status}`)}</td>
                  <td>{when(rev.effective_from)}</td>
                  <td>{when(rev.effective_to)}</td>
                  <td>{rev.change_reason || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {selected && specFields && (
        <>
          <RecordDetail
            title={`${t('engineering.detail.specTitle')} — ${t('engineering.fields.revisionNumber')} ${selected.revision_number}`}
            fields={specFields}
          />

          <Card title={t('engineering.detail.layersTitle')}>
            {layers.length === 0 ? (
              <p>{t('masterData.empty')}</p>
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>{t('engineering.layers.material')}</th>
                      <th>{t('engineering.layers.function')}</th>
                      <th>{t('engineering.layers.micron')}</th>
                      <th>{t('engineering.layers.tolerance')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {layers.map((l) => (
                      <tr key={l.id}>
                        <td>{l.sequence}</td>
                        <td>{labelFor(l.material)}</td>
                        <td>{l.function}</td>
                        <td>{l.micron ?? '—'}</td>
                        <td>{formatTolerance(l.micron_tol_low, l.micron_tol_high)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          <Card title={t('engineering.detail.colorsTitle')}>
            {colors.length === 0 ? (
              <p>{t('masterData.empty')}</p>
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>{t('engineering.colors.colorName')}</th>
                      <th>{t('engineering.colors.ink')}</th>
                      <th>{t('engineering.colors.alternativeInk')}</th>
                      <th>{t('engineering.colors.coverage')}</th>
                      <th>{t('engineering.colors.deltaETolerance')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {colors.map((c) => (
                      <tr key={c.id}>
                        <td>{c.sequence}</td>
                        <td>{c.color_name}</td>
                        <td>{labelFor(c.ink)}</td>
                        <td>{labelFor(c.alternative_ink)}</td>
                        <td>{c.coverage_pct ?? '—'}</td>
                        <td>{c.delta_e_tol ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          <Card title={t('engineering.detail.paramsTitle')}>
            {params.length === 0 ? (
              <p>{t('masterData.empty')}</p>
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{t('engineering.params.key')}</th>
                      <th>{t('engineering.params.datatype')}</th>
                      <th>{t('engineering.params.value')}</th>
                      <th>{t('engineering.params.unit')}</th>
                      <th>{t('engineering.params.tolerance')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {params.map((p) => (
                      <tr key={p.id}>
                        <td>{p.key}</td>
                        <td>{p.datatype}</td>
                        <td>{formatParameterValue(p)}</td>
                        <td>{p.unit || '—'}</td>
                        <td>
                          {p.tol_low == null && p.tol_high == null
                            ? '—'
                            : `${p.tol_low ?? ''} … ${p.tol_high ?? ''}`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}

      <AuditHistoryPanel entityType="engineering.CustomerProduct" entityId={product.id} />

      {hasPermission('documents.attachment.view') && (
        <AttachmentPanel entityType="engineering.CustomerProduct" entityId={product.id} />
      )}

      <div className="form-actions">
        <a className="link-back" onClick={() => window.history.back()} href="#back">
          ← {t('common.back')}
        </a>
      </div>
    </div>
  );
}
