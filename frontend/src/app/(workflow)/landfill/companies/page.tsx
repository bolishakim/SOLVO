import { ComingSoon } from '@/components/shared/coming-soon';
import { t } from '@/lib/translations';

export default function CompaniesPage() {
  return <ComingSoon title={t.pages.companies.title} description={t.pages.companies.description} />;
}
