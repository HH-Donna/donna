import { createClient } from '@/app/utils/supabase/server'
import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    const supabase = await createClient()
    
    const { data: { user }, error: userError } = await supabase.auth.getUser()

    if (userError || !user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await request.json()
    const { phone, companyName } = body

    if (!phone || !companyName) {
      return NextResponse.json(
        { error: 'Phone number and company name are required' },
        { status: 400 }
      )
    }

    const { error: profileError } = await supabase
      .from('profiles')
      .upsert({
        id: user.id,
        phone,
        company_name: companyName,
        updated_at: new Date().toISOString()
      })

    if (profileError) {
      return NextResponse.json({ error: profileError.message }, { status: 400 })
    }

    const { error: metadataError } = await supabase.auth.updateUser({
      data: {
        onboarding_completed: true
      }
    })

    if (metadataError) {
      console.error('Failed to update user metadata:', metadataError)
    }

    return NextResponse.json({ 
      message: 'Profile updated successfully',
      user: {
        phone,
        companyName
      }
    })
  } catch (error) {
    console.error('Onboarding error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}