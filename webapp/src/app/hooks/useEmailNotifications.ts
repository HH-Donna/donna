'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/app/utils/supabase/client'
import { toast } from 'sonner'

interface EmailNotification {
  id: string
  sender: string
  subject: string
  body: string
  received_at: string
  status: 'processing' | 'completed' | 'flagged'
  label: string
  user_id: string
}

export function useEmailNotifications(userId: string) {
  const [newEmailCount, setNewEmailCount] = useState(0)
  const [latestEmails, setLatestEmails] = useState<EmailNotification[]>([])

  useEffect(() => {
    if (!userId) return

    const supabase = createClient()

    const channel = supabase
      .channel(`emails-${userId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'emails',
          filter: `user_id=eq.${userId}`
        },
        (payload: any) => {
          const newEmail = payload.new as EmailNotification
          console.log('New email received!', newEmail)
          
          setLatestEmails(prev => [newEmail, ...prev.slice(0, 9)]) 
          setNewEmailCount(prev => prev + 1)
          
          toast.success('New Email Received!', {
            description: `From: ${newEmail.sender}`,
            action: {
              label: 'View',
              onClick: () => {
                window.location.reload()
              }
            }
          })
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'emails',
          filter: `user_id=eq.${userId}`
        },
        (payload: any) => {
          const updatedEmail = payload.new as EmailNotification
          console.log('Email updated', updatedEmail)
          
          setLatestEmails(prev => 
            prev.map(email => 
              email.id === updatedEmail.id ? updatedEmail : email
            )
          )
        
          if (payload.old?.status !== updatedEmail.status) {
            toast.info('Email Status Updated', {
              description: `${updatedEmail.subject} is now ${updatedEmail.status}`
            })
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [userId])

  const clearNotifications = () => {
    setNewEmailCount(0)
  }

  return {
    newEmailCount,
    latestEmails,
    clearNotifications
  }
}
