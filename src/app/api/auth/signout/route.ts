import { createClient } from '@/app/utils/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const supabase = await createClient()
  const { origin } = new URL(request.url)

  const { error } = await supabase.auth.signOut()

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 })
  }

  return NextResponse.json({ message: 'Signed out successfully' })
}

export async function GET(request: NextRequest) {
  const supabase = await createClient()
  const { origin } = new URL(request.url)

  await supabase.auth.signOut()
  return NextResponse.redirect(`${origin}/`)
}
