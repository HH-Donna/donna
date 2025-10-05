import { useState, useRef, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface Email {
  id: number
  sender: string
  subject: string
  body: string
  company: string
  status: 'flagged' | 'resolved' | 'pending' | 'processed'
  received_at: string
  label: string
}

interface EmailListProps {
  emails: Email[]
  onEmailClick?: (email: Email) => void
}

// Component for expandable content with smooth animation
function ExpandableContent({ isExpanded, children }: { isExpanded: boolean; children: React.ReactNode }) {
  const contentRef = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState(0)

  useEffect(() => {
    if (contentRef.current) {
      setHeight(isExpanded ? contentRef.current.scrollHeight : 0)
    }
  }, [isExpanded, children])

  return (
    <div 
      className="overflow-hidden transition-all duration-300 ease-in-out"
      style={{ height: `${height}px` }}
    >
      <div ref={contentRef}>
        {children}
      </div>
    </div>
  )
}

export default function EmailList({ emails, onEmailClick }: EmailListProps) {
  const [expandedEmails, setExpandedEmails] = useState<Set<number>>(new Set())
  const [logsByEmail, setLogsByEmail] = useState<Record<number, any[]>>({})

  // Render exactly the emails provided; no placeholders

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'processed':
        return 'bg-gray-100 text-gray-800 border-gray-300'
      case 'flagged':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'resolved':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300'
      case 'pending':
        return 'bg-amber-100 text-amber-800 border-amber-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getLabelColor = (label: string) => {
    switch (label.toLowerCase()) {
      // Fraud detection labels
      case 'safe':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'unsure':
        return 'bg-amber-100 text-amber-800 border-amber-300'
      case 'fraudulent':
        return 'bg-red-100 text-red-800 border-red-300'
      // Email type labels  
      case 'invoice':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'wire transfer':
        return 'bg-purple-100 text-purple-800 border-purple-300'
      case 'payment':
        return 'bg-indigo-100 text-indigo-800 border-indigo-300'
      case 'bank details':
        return 'bg-pink-100 text-pink-800 border-pink-300'
      case 'account update':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'billing':
        return 'bg-teal-100 text-teal-800 border-teal-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)

    if (diffInHours < 24) {
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      })
    }
  }

  const toggleExpanded = (emailId: number) => {
    setExpandedEmails(prev => {
      const newSet = new Set(prev)
      if (newSet.has(emailId)) {
        newSet.delete(emailId)
      } else {
        newSet.add(emailId)
      }
      return newSet
    })
    
    // Call onEmailClick when expanding (optional - remove if not needed)
    const email = emails.find(e => e.id === emailId)
    if (email && !expandedEmails.has(emailId)) {
      onEmailClick?.(email)
      // Lazy-fetch fraud logs for this email when expanding
      if (!logsByEmail[emailId]) {
        fetch(`/api/logs/${encodeURIComponent(String(emailId))}`)
          .then(r => r.ok ? r.json() : Promise.reject(new Error('failed')))
          .then(json => {
            const logs = Array.isArray(json?.logs) ? json.logs : []
            setLogsByEmail(prev => ({ ...prev, [emailId]: logs }))
          })
          .catch(() => {
            setLogsByEmail(prev => ({ ...prev, [emailId]: [] }))
          })
      }
    }
  }

  const orderedSteps = [
    'gemini_analysis',
    'domain_check',
    'company_verification',
    'final_decision'
  ] as const

  const stepLabel: Record<string, string> = {
    gemini_analysis: 'AI Analysis',
    domain_check: 'Domain Check',
    company_verification: 'Company Verification',
    final_decision: 'Final Decision'
  }

  function buildStepPanels(emailId: number) {
    const logs = logsByEmail[emailId] || []
    const byStep: Record<string, any> = {}
    for (const log of logs) {
      const key = String(log.step || '').toLowerCase()
      if (!byStep[key]) byStep[key] = log
    }
    const panels = orderedSteps.map(step => byStep[step] || null)
    return panels
  }

  return (
    <div className="space-y-2 mx-6 mb-6">
      {emails.map((email) => {
        const isExpanded = expandedEmails.has(email.id)
        
        return (
          <div
            key={email.id}
            className="bg-white border border-gray-300 rounded-lg hover:shadow-md hover:border-gray-400 transition-all duration-200"
          >
            <div
              className="flex items-center p-4 cursor-pointer group"
              onClick={() => toggleExpanded(email.id)}
            >
              {/* Left: Subject and Sender */}
              <div className="flex-1 min-w-0 mr-4">
                <p className="font-semibold text-[15px] text-gray-900 truncate leading-tight">
                  {email.subject}
                </p>
                <p className="text-xs text-gray-600 mt-1 font-medium">
                  {email.sender}
                </p>
              </div>

              {/* Center: Status and Label - Fixed Width */}
              <div className="flex items-center gap-4 mr-6">
                <div className="w-24 flex justify-end">
                  <Badge 
                    variant="outline"
                    className={`${getStatusColor(email.status)} text-xs px-2.5 py-0.5 font-semibold`}
                  >
                    {email.status.charAt(0).toUpperCase() + email.status.slice(1)}
                  </Badge>
                </div>
                <div className="w-32 flex justify-start">
                  <Badge 
                    variant="outline"
                    className={`${getLabelColor(email.label)} text-xs px-2.5 py-0.5 font-semibold`}
                  >
                    {email.label.charAt(0).toUpperCase() + email.label.slice(1)}
                  </Badge>
                </div>
              </div>

              {/* Right: Time and Chevron - Fixed Width */}
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-600 font-medium whitespace-nowrap w-16 text-right">
                  {formatDate(email.received_at)}
                </span>
                <div className="p-1.5 rounded-lg group-hover:bg-gray-100 transition-colors">
                  <div className={`transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}>
                    <ChevronRight className="h-4 w-4 text-gray-600" 
                      style={{
                        transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                        transition: 'transform 0.3s ease'
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Expanded Content with Animation */}
            <ExpandableContent isExpanded={isExpanded}>
              <div className="px-4 pb-4">
                <div className="border-t border-gray-200 pt-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Company</span>
                    <span className="text-sm text-gray-900 font-medium">{email.company}</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Received</span>
                    <span className="text-sm text-gray-900 font-medium">
                      {new Date(email.received_at).toLocaleString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                        hour12: true
                      })}
                    </span>
                  </div>
                  
                  <div className="pt-2">
                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Preview</span>
                    <div className="mt-2 p-3 bg-gray-100 rounded-lg">
                      <p className="text-sm text-gray-800 leading-relaxed line-clamp-3">
                        {email.body}
                      </p>
                    </div>
                  </div>

                  {/* Analysis Steps: 4 columns horizontally, full-height, with clear vertical dividers */}
                  <div className="mt-3">
                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Analysis Steps</span>
                    <div className="mt-2 flex divide-x divide-gray-200 rounded-lg border border-gray-200 overflow-hidden min-h-[128px] items-stretch w-full">
                      {buildStepPanels(email.id).map((log, idx) => (
                        <div key={idx} className="relative flex-1 p-3 flex flex-col items-center justify-center text-center">
                          {/* Internal centered gradient line, not touching edges */}
                          <div className="pointer-events-none absolute left-1/2 top-2 bottom-2 -translate-x-1/2">
                            <div className="w-px h-full bg-gradient-to-b from-transparent via-gray-300 to-transparent" />
                          </div>

                          <div className="text-[11px] font-semibold text-gray-700 mb-1">
                            {stepLabel[orderedSteps[idx]]}
                          </div>
                          {log ? (
                            <div className="text-xs text-gray-700 leading-snug whitespace-pre-wrap break-words">
                              {String(log.reasoning || '').slice(0, 280)}
                            </div>
                          ) : (
                            <div className="text-xs text-gray-400">—</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </ExpandableContent>
          </div>
        )
      })}
    </div>
  )
}