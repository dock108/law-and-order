import { getServerSession } from 'next-auth/next';
import { redirect } from 'next/navigation';

export default async function RootPage() {
  const session = await getServerSession();

  if (session) {
    // User is logged in, redirect to the dashboard
    redirect('/dashboard');
  } else {
    // User is not logged in, redirect to the sign-in page
    // NextAuth provides a default sign-in page at this path for Credentials provider
    redirect('/api/auth/signin');
  }

  // This part should ideally not be reached due to redirects,
  // but returning null or a simple loading indicator is good practice.
  return null;
}
