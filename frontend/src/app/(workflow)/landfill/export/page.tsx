import { ComingSoon } from '@/components/shared/coming-soon';
import { t } from '@/lib/translations';

export default function ExportPage() {
  return <ComingSoon title={t.pages.export.title} description={t.pages.export.description} />;
}
