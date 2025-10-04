import { createClient } from '@/app/utils/supabase/server'
import { NextResponse } from 'next/server'

export async function POST() {
  const supabase = await createClient()

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${'http://localhost:3000'}/api/auth/callback`,
      scopes: 'https://mail.google.com/ https://www.googleapis.com/auth/gmail.labels'
    },
  })

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 })
  }

  return NextResponse.json({ url: data.url })
}