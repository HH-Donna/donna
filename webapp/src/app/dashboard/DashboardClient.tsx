'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { DollarSign, ShieldCheck, Phone } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import DashboardNav from '../components/DashboardNav'
import EmailList from '../components/EmailList'
import EmailSearch from '../components/EmailSearch'
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
  const [searchQuery, setSearchQuery] = useState('')
  const [emails, setEmails] = useState(initialEmails)
  
  const { newEmailCount, latestEmails, clearNotifications } = useEmailNotifications(onboardingProps.userId)

  // Update emails when new ones arrive via real-time subscription
  useEffect(() => {
    if (latestEmails.length > 0) {
      setEmails(prevEmails => {
        // Create a map of existing emails for efficient lookup
        const existingEmailIds = new Set(prevEmails.map(e => e.id))
        
        // Filter out emails that already exist
        const newEmails = latestEmails.filter(email => !existingEmailIds.has(email.id))
        
        // Merge new emails at the beginning
        if (newEmails.length > 0) {
          return [...newEmails, ...prevEmails]
        }
        
        // Update existing emails if they've been modified
        return prevEmails.map(email => {
          const updatedEmail = latestEmails.find(e => e.id === email.id)
          return updatedEmail || email
        })
      })
    }
  }, [latestEmails])

  // Calculate metrics from current emails (including real-time updates)
  const calculateMetrics = () => {
    // Calculate total money saved from fraudulent and unsure emails
    const totalMoneySaved = emails
      .filter(email => email.label === 'fraudulent' || email.label === 'unsure')
      .reduce((sum, email) => sum + (email.amount || 0), 0)

    // Count total avoided scams (fraudulent + unsure emails)
    const totalAvoidedScams = emails.filter(
      email => email.label === 'fraudulent' || email.label === 'unsure'
    ).length

    // Calculate calls made in the past week
    // For now, using mock data - in production, this would come from a calls table
    const callsMadeThisWeek = 18

    return {
      totalMoneySaved,
      totalAvoidedScams,
      callsMadeThisWeek
    }
  }

  const metrics = calculateMetrics()

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

  // Process emails with memoization to avoid unnecessary recalculations
  const processedEmails = useMemo(() => {
    // Get IDs of the latest emails for marking as new
    const latestEmailIds = new Set(latestEmails.map(e => e.id))
    
    return emails.map((email: any) => ({
      id: email.id,
      sender: email.sender || '',
      subject: email.subject || '',
      body: email.body || '',
      company: email.company_id || email.company || 'Unknown', 
      status: email.status as 'flagged' | 'resolved' | 'pending' | 'processed',
      received_at: email.received_at || new Date().toISOString(),
      label: email.label || '',
      amount: email.amount || 0,
      isNew: latestEmailIds.has(email.id)
    }))
  }, [emails, latestEmails])

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
    // Clear notifications when user interacts with emails
    if (newEmailCount > 0) {
      clearNotifications()
    }
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
    <div className="min-h-screen bg-gray-50">
      <DashboardNav user={user} onLogout={handleLogout} />

      <div className="container mx-auto py-8">
        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 px-6">
          {/* Total Money Saved */}
          <Card className="bg-white border-gray-300 shadow-sm hover:shadow-md transition-shadow duration-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600">Total Money Saved</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    £{metrics.totalMoneySaved.toFixed(2)}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">From blocked fraudulent emails</p>
                </div>
                <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                  <DollarSign className="h-5 w-5 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Total Avoided Scams */}
          <Card className="bg-white border-gray-300 shadow-sm hover:shadow-md transition-shadow duration-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600">Total Avoided Scams</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {metrics.totalAvoidedScams}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">Fraudulent attempts blocked</p>
                </div>
                <div className="h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center">
                  <ShieldCheck className="h-5 w-5 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Calls Made This Week */}
          <Card className="bg-white border-gray-300 shadow-sm hover:shadow-md transition-shadow duration-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600">Calls Made This Week</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {metrics.callsMadeThisWeek}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">By Donna AI assistant</p>
                </div>
                <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                  <Phone className="h-5 w-5 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 px-6">
          {/* Left: Emails (2/3 width) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="mx-6">
              <h2 className="text-lg font-bold text-gray-900 tracking-tight mb-2">
                Emails
                {newEmailCount > 0 && (
                  <span className="ml-2 text-sm font-normal text-amber-600">
                    ({newEmailCount} new)
                  </span>
                )}
              </h2>
              <p className="text-sm text-gray-600 -mt-2 mb-4">Recent email activity and fraud detection</p>
            </div>
            <EmailSearch 
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              onFilterClick={handleFilterClick}
            />
            <EmailList emails={filteredEmails} onEmailClick={handleEmailClick} />
          </div>

          {/* Right: Legitimate Billers (1/3 width) */}
          <div className="lg:col-span-1 space-y-4">
            <LegitimateBillers 
              key="persistent-billers" 
              billers={legitimateBillers} 
            />
          </div>
        </div>
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