import { createClient } from '@/app/utils/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const supabase = await createClient()
  const { searchParams, origin } = new URL(request.url)
  
  // Get the redirect URL from query params or use default
  const redirectTo = searchParams.get('redirectTo') ?? `${origin}/auth/callback`
  
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo,
      queryParams: {
        access_type: 'offline',
        prompt: 'consent',
      },
    },
  })

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 })
  }

  return NextResponse.json({ url: data.url })
}

export async function GET(request: NextRequest) {
  const supabase = await createClient()
  const { searchParams, origin } = new URL(request.url)
  
  // Get the redirect URL from query params or use default
  const redirectTo = searchParams.get('redirectTo') ?? `${origin}/auth/callback`
  
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo,
      queryParams: {
        access_type: 'offline',
        prompt: 'consent',
      },
    },
  })

  if (error) {
    return NextResponse.redirect(`${origin}/auth/auth-code-error`)
  }

  if (data.url) {
    return NextResponse.redirect(data.url)
  }

  return NextResponse.redirect(`${origin}/auth/auth-code-error`)
}
