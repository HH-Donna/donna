import { redirect } from 'next/navigation'
import { createClient } from '@/app/utils/supabase/server'
import DashboardClient from './DashboardClient'

export default async function DashboardPage() {
  const supabase = await createClient()
  
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/')
  }

  const { data: profile, error: profileError } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single()

  if (profileError || !profile) {
    const needsOnboarding = true
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${apiUrl}/gmail/watch/setup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.API_TOKEN || 'test'}`
      },
      body: JSON.stringify({ user_uuid: user.id })
    })
      .then(res => res.json())
      .then(data => console.log(' Gmail watch setup:', data))
      .catch(err => console.error(' Gmail watch setup failed:', err))
    
    return (
      <DashboardClient 
        user={{
          name: user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0] || 'User',
          email: user.email || '',
          companyName: 'Pending Setup',
          initials: (user.user_metadata?.full_name || user.user_metadata?.name || user.email || 'U')
            .split(' ')
            .map((n: any) => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2),
          profileUrl: user.user_metadata?.avatar_url || user.user_metadata?.picture
        }}
        initialEmails={[]}
        companies={[]}
        needsOnboarding={needsOnboarding}
        onboardingProps={{
          userId: user.id,
          userEmail: user.email || ''
        }}
      />
    )
  }

  const hasPhone = !!profile?.phone
  const hasCompanyName = !!profile?.company_name
  const needsOnboarding = !hasPhone || !hasCompanyName

  if (needsOnboarding) {
    return (
      <DashboardClient 
        user={{
          name: user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0] || 'User',
          email: user.email || '',
          companyName: 'Pending Setup',
          initials: (user.user_metadata?.full_name || user.user_metadata?.name || user.email || 'U')
            .split(' ')
            .map((n: any) => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2),
          profileUrl: user.user_metadata?.avatar_url || user.user_metadata?.picture
        }}
        initialEmails={[]}
        companies={[]}
        needsOnboarding={needsOnboarding}
        onboardingProps={{
          userId: user.id,
          userEmail: user.email || ''
        }}
      />
    )
  }

  const { data: emails } = await supabase
    .from('emails')
    .select('*')
    .order('received_at', { ascending: false })
    .limit(50)

  const { data: companies } = await supabase
    .from('companies')
    .select('*')

  const userName = user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0] || 'User'
  const companyName = profile?.company_name
  
  const userData = {
    name: userName,
    email: user.email || '',
    companyName: companyName,
    initials: userName
      .split(' ')
      .map((n: any) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2),
    profileUrl: user.user_metadata?.avatar_url || user.user_metadata?.picture
  }


  return (
    <DashboardClient 
      user={userData}
      initialEmails={emails || []}
      companies={companies || []}
      needsOnboarding={needsOnboarding}
      onboardingProps={{
        userId: user.id,
        userEmail: user.email || ''
      }}
    />
  )
}