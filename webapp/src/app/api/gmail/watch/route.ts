import { createClient } from '@/app/utils/supabase/server'
import { NextResponse } from 'next/server'

export async function POST() {
  const supabase = await createClient()
  
  // Get current user
  const { data: { user }, error: userError } = await supabase.auth.getUser()
  
  if (userError || !user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    // Call backend API to setup Gmail watch
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/gmail/watch/setup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.API_TOKEN || 'test'}`
      },
      body: JSON.stringify({
        user_uuid: user.id
      })
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json({ error: data.detail || 'Failed to setup Gmail watch' }, { status: response.status })
    }

    return NextResponse.json({
      success: true,
      message: data.message,
      history_id: data.history_id,
      expires_in_days: data.expires_in_days
    })

  } catch (error) {
    console.error('Error setting up Gmail watch:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
