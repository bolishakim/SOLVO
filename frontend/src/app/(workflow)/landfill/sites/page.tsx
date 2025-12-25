import { ComingSoon } from '@/components/shared/coming-soon';
import { t } from '@/lib/translations';

export default function SitesPage() {
  return <ComingSoon title={t.pages.sites.title} description={t.pages.sites.description} />;
}
