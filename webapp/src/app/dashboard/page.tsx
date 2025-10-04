import { redirect } from 'next/navigation'
import { createClient } from '@/app/utils/supabase/server'
import DashboardClient from './DashboardClient'

export default async function DashboardPage() {
  const supabase = await createClient()
  
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/')
  }

  const { data: emails } = await supabase
    .from('emails')
    .select('*')
    .order('received_at', { ascending: false })
    .limit(50)

  const { data: companies } = await supabase
    .from('companies')
    .select('*')

  const userData = {
    name: user.user_metadata?.name || user.email?.split('@')[0] || 'User',
    email: user.email || '',
    initials: (user.user_metadata?.name || user.email || 'U')
      .split(' ')
      .map((n: any) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2),
    profileUrl: user.user_metadata?.avatar_url || ''
  }

  return (
    <DashboardClient 
      user={userData}
      initialEmails={emails || []}
      companies={companies || []}
    />
  )
}