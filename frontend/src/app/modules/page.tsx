"use client";

import { redirect } from 'next/navigation';

export default function PageWrapper() {
  // This is a legacy route, permanently redirect to the correct dashboard URL.
  // Using the redirect function from next/navigation is the recommended approach.
  redirect('/dashboard');
  return null; // This component will not render anything.
}
