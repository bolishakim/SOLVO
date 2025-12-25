'use client';

import { useEffect, useState } from 'react';
import { Toaster } from '@/components/ui/sonner';

/**
 * Client-only Toaster wrapper that prevents hydration mismatch.
 * The Toaster only renders after the component has mounted on the client.
 */
export function ClientToaster() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return <Toaster richColors position="top-right" />;
}
