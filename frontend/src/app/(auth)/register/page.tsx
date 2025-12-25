'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function RegisterPage() {
  const router = useRouter();

  useEffect(() => {
    // Public registration is disabled - redirect to login
    router.replace('/login');
  }, [router]);

  return null;
}
