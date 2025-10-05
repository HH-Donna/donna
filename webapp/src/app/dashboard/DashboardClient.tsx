'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Mail, TrendingUp, Bell } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import DashboardNav from '../components/DashboardNav'
import EmailList from '../components/EmailList'
import EmailSearch from '../components/EmailSearch'
import Analytics from '../components/Analytics'
import LegitimateBillers from '../components/LegitimateBillers'
import OnboardingForm from '../components/OnboardingForm'
import { useEmailNotifications } from '../hooks/useEmailNotifications'


interface DashboardClientProps {
  user: {
    name: string
    email: string
    companyName: string
    initials: string
    profileUrl?: string
  }
  initialEmails: any[]
  companies: any[]
  needsOnboarding: boolean
  onboardingProps: {
    userId: string
    userEmail: string
  }
}

export default function DashboardClient({ user, initialEmails, companies, needsOnboarding, onboardingProps }: DashboardClientProps) {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState('emails')
  const [searchQuery, setSearchQuery] = useState('')
  
  const { newEmailCount, latestEmails, clearNotifications } = useEmailNotifications(onboardingProps.userId)

  const legitimateBillers = companies.map((company: any) => ({
    id: company.id || company.name,
    name: company.name || 'Unknown',
    domain: company.domain || '',
    billing_address: company.billing_address,
    created_at: company.created_at || new Date().toISOString(),
    profile_picture_url: company.profile_picture_url,
    payment_method: company.payment_method,
    biller_billing_details: company.biller_billing_details,
    frequency: company.frequency,
    total_invoices: company.total_invoices,
    source_email_ids: company.source_email_ids,
    user_id: company.user_id,
    updated_at: company.updated_at || new Date().toISOString(),
    user_billing_details: company.user_billing_details,
    contact_emails: company.contact_emails,
    user_account_number: company.user_account_number,
    biller_phone_number: company.biller_phone_number
  }))

  const processedEmails = initialEmails.map((email: any) => ({
    id: email.id,
    sender: email.sender || '',
    subject: email.subject || '',
    body: email.body || '',
    company: email.company_id || 'Unknown', 
    status: email.status as 'flagged' | 'resolved' | 'pending',
    received_at: email.received_at || new Date().toISOString(),
    label: email.label || ''
  }))

  const stats = {
    totalEmails: initialEmails.length,
    flagged: initialEmails.filter(e => e.status === 'flagged').length,
    agentCalls: 18, 
    resolved: initialEmails.filter(e => e.status === 'resolved').length,
    successRate: initialEmails.length > 0 
      ? Math.round((initialEmails.filter(e => e.status === 'resolved').length / initialEmails.length) * 100)
      : 0
  }

  const emailTrendData = [
    { month: 'Jul', emails: 45 },
    { month: 'Aug', emails: 52 },
    { month: 'Sep', emails: 61 },
    { month: 'Oct', emails: 89 }
  ]

  const statusData = [
    { name: 'Resolved', value: stats.resolved, color: '#374151' },
    { name: 'Flagged', value: stats.flagged, color: '#f59e0b' },
    { name: 'Pending', value: stats.totalEmails - stats.resolved - stats.flagged, color: '#9ca3af' }
  ]

  const callsData = [
    { day: 'Mon', calls: 3 },
    { day: 'Tue', calls: 2 },
    { day: 'Wed', calls: 4 },
    { day: 'Thu', calls: 5 },
    { day: 'Fri', calls: 2 },
    { day: 'Sat', calls: 1 },
    { day: 'Sun', calls: 1 }
  ]

  const handleLogout = async () => {
    try {
      const response = await fetch('/api/logout', {
        method: 'POST'
      })

      if (response.ok) {
        router.push('/')
        router.refresh()
      }
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  const handleEmailClick = (email: any) => {
    console.log('Email clicked:', email)
  }

  const handleFilterClick = () => {
    console.log('Filter clicked')
  }
  const filteredEmails = processedEmails.filter((email: any) => 
    email.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
    email.sender.toLowerCase().includes(searchQuery.toLowerCase()) ||
    email.company.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-neutral-50">
      <DashboardNav user={user} onLogout={handleLogout} />

      <div className="container mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-white border border-gray-200">
            <TabsTrigger
              value="emails" 
              className="data-[state=active]:bg-amber-500 data-[state=active]:text-white"
              onClick={() => {
                if (activeTab === 'emails') clearNotifications()
              }}
            >
              <div className="flex items-center">
                <Mail className="h-4 w-4 mr-2" />
                Email List
                {newEmailCount > 0 && (
                  <Badge variant="destructive" className="ml-2 text-xs px-2 py-1">
                    {newEmailCount}
                  </Badge>
                )}
              </div>
            </TabsTrigger>
            <TabsTrigger 
              value="analytics" 
              className="data-[state=active]:bg-amber-500 data-[state=active]:text-white"
            >
              <TrendingUp className="h-4 w-4 mr-2" />
              Analytics
            </TabsTrigger>
          </TabsList>

          <TabsContent value="emails" className="space-y-6">
            <LegitimateBillers 
              key="persistent-billers" 
              billers={legitimateBillers} 
            />
            <EmailSearch 
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              onFilterClick={handleFilterClick}
            />
            <EmailList emails={filteredEmails} onEmailClick={handleEmailClick} />
          </TabsContent>

          <TabsContent value="analytics">
            <Analytics
              stats={stats}
              emailTrendData={emailTrendData}
              statusData={statusData}
              callsData={callsData}
            />
          </TabsContent>
        </Tabs>
      </div>

      {/* Onboarding Modal Overlay */}
      {needsOnboarding && (
        <OnboardingForm 
          userId={onboardingProps.userId}
          userEmail={onboardingProps.userEmail}
        />
      )}
    </div>
  )
}