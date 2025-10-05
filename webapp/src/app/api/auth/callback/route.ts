import { createClient } from '@/app/utils/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')

  if (code) {
    const supabase = await createClient()
    
    const { data, error } = await supabase.auth.exchangeCodeForSession(code)

    if (error) {
      return NextResponse.redirect(`${requestUrl.origin}?error=${error.message}`)
    }

    if (data?.session?.user) {
      const user = data.session.user
      const session = data.session
      
      const providerToken = session.provider_token
      const providerRefreshToken = session.provider_refresh_token
      
      
      // Check if we have Gmail-related scopes (including People API for profile pictures and modify for watch)
      const scopes = session.provider_token ? [
        'https://mail.google.com/', 
        'https://www.googleapis.com/auth/gmail.labels',
        'https://www.googleapis.com/auth/contacts.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
      ] : []
      
      if (providerToken && user.id) {
        try {
          console.log('Storing OAuth tokens:', {
            has_refresh_token: !!providerRefreshToken,
            scopes: scopes.length
          })
          
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/oauth/store`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${process.env.API_TOKEN || 'test'}`
            },
            body: JSON.stringify({
              user_id: user.id,
              provider: 'google',
              access_token: providerToken,
              refresh_token: providerRefreshToken || '',
              scopes: scopes,
            })
          })
          
          if (!response.ok) {
            console.error('Failed to store OAuth tokens:', await response.text())
          } else {
            console.log('OAuth tokens stored successfully')
          }
        } catch (err) {
          console.error('Error storing OAuth tokens:', err)
        }
      }
    }

    return NextResponse.redirect(`${requestUrl.origin}/dashboard`)
  }

  return NextResponse.redirect(requestUrl.origin)
}