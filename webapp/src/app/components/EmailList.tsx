import { useState, useRef, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface Email {
  id: number | string
  sender: string
  subject: string
  body: string
  company: string
  status: 'flagged' | 'resolved' | 'pending' | 'processed' | 'processing' | 'completed'
  received_at: string
  label: string
  isNew?: boolean
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
  const [expandedEmails, setExpandedEmails] = useState<Set<string>>(new Set())
  const [logsByEmail, setLogsByEmail] = useState<Record<string, any[]>>({})

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

  const cleanEmailBody = (body: string): string => {
    if (!body) return 'No content available'

    let cleaned = body
    
    // Remove everything from "=== ATTACHMENTS ===" onwards
    const attachmentIndex = cleaned.indexOf('=== ATTACHMENTS ===')
    if (attachmentIndex !== -1) {
      cleaned = cleaned.substring(0, attachmentIndex)
    }
    
    // Remove HTML tags
    cleaned = cleaned.replace(/<[^>]*>/g, '')
    
    // Decode common HTML entities
    const htmlEntities: Record<string, string> = {
      '&nbsp;': ' ',
      '&amp;': '&',
      '&lt;': '<',
      '&gt;': '>',
      '&quot;': '"',
      '&#39;': "'",
      '&apos;': "'",
      '&ndash;': '\u2013',
      '&mdash;': '\u2014',
      '&rsquo;': '\u2019',
      '&lsquo;': '\u2018',
      '&rdquo;': '\u201D',
      '&ldquo;': '\u201C'
    }
    
    Object.entries(htmlEntities).forEach(([entity, char]) => {
      cleaned = cleaned.replace(new RegExp(entity, 'g'), char)
    })
    
    // Decode numeric HTML entities
    cleaned = cleaned.replace(/&#(\d+);/g, (match, dec) => String.fromCharCode(dec))
    cleaned = cleaned.replace(/&#x([0-9A-Fa-f]+);/g, (match, hex) => String.fromCharCode(parseInt(hex, 16)))
    
    // Remove URLs (optional - keeps text cleaner)
    cleaned = cleaned.replace(/https?:\/\/[^\s]+/g, '')
    
    // Remove email addresses in <> brackets
    cleaned = cleaned.replace(/<[^@\s]+@[^@\s]+\.[^@\s]+>/g, '')
    
    // Remove lines that are just dashes/separators (4 or more dashes in a row)
    cleaned = cleaned.replace(/[\r\n\s]*[-=_*]{4,}[\r\n\s]*/g, ' ')
    
    // Remove excessive whitespace, newlines, tabs
    cleaned = cleaned.replace(/[\r\n\t]+/g, ' ')
    cleaned = cleaned.replace(/\s{2,}/g, ' ')
    
    // Remove special characters that are often formatting artifacts
    cleaned = cleaned.replace(/[|~`\[\]{}]/g, '')
    
    // Remove multiple punctuation
    cleaned = cleaned.replace(/([.!?])\1+/g, '$1')
    
    // Trim and ensure we have content
    cleaned = cleaned.trim()
    
    return cleaned || 'No readable content available'
  }

  const toggleExpanded = (emailId: number | string) => {
    const idKey = String(emailId)
    setExpandedEmails(prev => {
      const newSet = new Set(prev)
      if (newSet.has(idKey)) {
        newSet.delete(idKey)
      } else {
        newSet.add(idKey)
      }
      return newSet
    })
    
    // Call onEmailClick when expanding (optional - remove if not needed)
    const email = emails.find(e => String(e.id) === idKey)
    if (email && !expandedEmails.has(idKey)) {
      onEmailClick?.(email)
      // Lazy-fetch fraud logs for this email when expanding
      if (!logsByEmail[idKey]) {
        console.log('🔍 Fetching logs for email ID:', idKey)
        fetch(`/api/logs/${encodeURIComponent(idKey)}`)
          .then(r => {
            console.log('📡 API Response status:', r.status)
            return r.ok ? r.json() : Promise.reject(new Error('failed'))
          })
          .then(json => {
            console.log('📊 API Response JSON:', json)
            const logs = Array.isArray(json?.logs) ? json.logs : []
            console.log('✅ Parsed logs:', logs)
            setLogsByEmail(prev => ({ ...prev, [idKey]: logs }))
          })
          .catch((err) => {
            console.error('❌ Error fetching logs:', err)
            setLogsByEmail(prev => ({ ...prev, [idKey]: [] }))
          })
      } else {
        console.log('📋 Logs already cached for email ID:', idKey, logsByEmail[idKey])
      }
    }
  }

  const orderedSteps = [
    'domain_check',
    'company_verification',
    'gemini_analysis',
    'final_decision'
  ] as const

  const stepLabel: Record<string, string> = {
    domain_check: 'Domain Check',
    company_verification: 'Company Verification',
    gemini_analysis: 'AI Analysis',
    final_decision: 'Final Decision'
  }

  function buildStepPanels(emailId: number | string) {
    const idKey = String(emailId)
    const logs = logsByEmail[idKey] || []
    console.log('🏗️ Building step panels for email:', idKey)
    console.log('📦 All logs for this email:', logs)
    console.log('📚 All logsByEmail state:', logsByEmail)
    
    const byStep: Record<string, any> = {}
    for (const log of logs) {
      const key = String(log.step || '').toLowerCase()
      if (!byStep[key]) byStep[key] = log
      console.log(`  📌 Mapping step "${key}" to log:`, log)
    }
    console.log('🗂️ Logs organized by step:', byStep)
    
    const panels = orderedSteps.map(step => byStep[step] || null)
    console.log('📋 Final panels array:', panels)
    return panels
  }

  return (
    <div className="space-y-2 mx-6 mb-6">
      {emails.map((email) => {
        const isExpanded = expandedEmails.has(String(email.id))
        return (
          <div
            key={email.id}
            className={`bg-white border rounded-lg hover:shadow-md transition-all duration-200 ${
              email.isNew 
                ? 'border-amber-400 shadow-amber-100 shadow-md animate-pulse-once' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
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
                        {cleanEmailBody(email.body)}
                      </p>
                    </div>
                  </div>

                  {/* Analysis Steps: 4 columns horizontally, full-height, with clear vertical dividers */}
                  <div className="mt-3">
                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Analysis Steps</span>
                    <div className="mt-2 flex divide-x divide-gray-200 rounded-lg border border-gray-200 overflow-hidden min-h-[128px] items-stretch w-full">
                      {buildStepPanels(email.id).map((log, idx) => (
                        <div key={idx} className="relative flex-1 p-3 flex flex-col text-center">
                          {/* Internal centered gradient line, not touching edges */}
                          <div className="pointer-events-none absolute left-1/2 top-2 bottom-2 -translate-x-1/2">
                            <div className="w-px h-full bg-gradient-to-b from-transparent via-gray-300 to-transparent" />
                          </div>

                          <div className="text-[11px] font-semibold text-gray-700 mb-2">
                            {stepLabel[orderedSteps[idx]]}
                          </div>
                          {log ? (
                            <div className="flex flex-col gap-2 text-left">
                              {log.decision && (
                                <div className="flex items-center gap-1.5 justify-center">
                                  <span className="text-[10px] font-semibold text-gray-500 uppercase">Decision:</span>
                                  <Badge 
                                    variant="outline"
                                    className={`${
                                      log.decision.toLowerCase() === 'safe' ? 'bg-green-100 text-green-800 border-green-300' :
                                      log.decision.toLowerCase() === 'fraudulent' ? 'bg-red-100 text-red-800 border-red-300' :
                                      'bg-amber-100 text-amber-800 border-amber-300'
                                    } text-[10px] px-1.5 py-0 font-semibold`}
                                  >
                                    {log.decision}
                                  </Badge>
                                </div>
                              )}
                              {log.confidence !== undefined && log.confidence !== null && (
                                <div className="text-[10px] text-gray-600 text-center">
                                  <span className="font-semibold">Confidence:</span> {Math.round(log.confidence * 100)}%
                                </div>
                              )}
                              {log.reasoning && (
                                <div className="text-[11px] text-gray-700 leading-snug">
                                  {String(log.reasoning).slice(0, 200)}
                                  {String(log.reasoning).length > 200 && '...'}
                                </div>
                              )}
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