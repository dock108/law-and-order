import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl) {
  throw new Error('Missing environment variable: NEXT_PUBLIC_SUPABASE_URL');
}
if (!supabaseServiceKey) {
  // Only critical on server-side where service key is needed for elevated privileges
  console.warn(
    'Missing environment variable: SUPABASE_SERVICE_ROLE_KEY. Storage operations requiring admin privileges may fail.'
  );
}

// Create a Supabase client configured to use the service role key
// This client bypasses RLS and should ONLY be used on the server.
export const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey!, {
    auth: {
        // prevent Supabase client from storing cookies/session data
        // essential for server-side operations where you don't want user sessions
        persistSession: false,
        autoRefreshToken: false,
        detectSessionInUrl: false,
    }
});

// Note: If you need a client-side Supabase instance later that *respects* RLS,
// you would create another client using the anon key:
// import { createBrowserClient } from '@supabase/ssr' // for client components
// export const supabaseBrowser = createBrowserClient(supabaseUrl, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!) 