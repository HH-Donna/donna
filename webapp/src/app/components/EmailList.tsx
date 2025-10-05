import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface Email {
  id: number
  sender: string
  subject: string
  body: string
  company: string
  status: 'flagged' | 'resolved' | 'pending'
  received_at: string
  label: string
}

interface EmailListProps {
  emails: Email[]
  onEmailClick?: (email: Email) => void
}

export default function EmailList({ emails, onEmailClick }: EmailListProps) {
  const [expandedEmails, setExpandedEmails] = useState<Set<number>>(new Set())

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'flagged':
        return 'bg-amber-500 text-white'
      case 'resolved':
        return 'bg-green-500 text-white'
      case 'pending':
        return 'bg-yellow-500 text-white'
      default:
        return 'bg-gray-500 text-white'
    }
  }

  const getLabelColor = (label: string) => {
    switch (label.toLowerCase()) {
      case 'invoice':
        return 'bg-blue-100 text-blue-700 border-blue-200'
      case 'wire transfer':
        return 'bg-purple-100 text-purple-700 border-purple-200'
      case 'payment':
        return 'bg-indigo-100 text-indigo-700 border-indigo-200'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
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

  const toggleExpanded = (emailId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    setExpandedEmails(prev => {
      const newSet = new Set(prev)
      if (newSet.has(emailId)) {
        newSet.delete(emailId)
      } else {
        newSet.add(emailId)
      }
      return newSet
    })
  }

  return (
    <div className="space-y-2 mx-6">
      {emails.map((email) => {
        const isExpanded = expandedEmails.has(email.id)
        
        return (
          <div
            key={email.id}
            className="bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-all"
          >
            <div
              className="flex items-center justify-between p-3 cursor-pointer"
              onClick={() => onEmailClick?.(email)}
            >
              {/* Left: Subject and Sender */}
              <div className="flex-1 min-w-0 mr-4">
                <p className="font-medium text-sm text-gray-900 truncate">{email.subject}</p>
                <p className="text-xs text-gray-500 mt-0.5">From: {email.sender}</p>
              </div>

              {/* Center: Status and Label */}
              <div className="flex items-center gap-2 mr-4">
                <Badge className={`${getStatusColor(email.status)} text-xs px-2 py-0.5 border-0`}>
                  {email.status}
                </Badge>
                <Badge variant="outline" className={`${getLabelColor(email.label)} text-xs px-2 py-0.5`}>
                  {email.label}
                </Badge>
              </div>

              {/* Right: Time and Chevron */}
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500 whitespace-nowrap">
                  {formatDate(email.received_at)}
                </span>
                <button
                  onClick={(e) => toggleExpanded(email.id, e)}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                  aria-label={isExpanded ? "Collapse" : "Expand"}
                >
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-gray-400" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  )}
                </button>
              </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
              <div className="px-3 pb-3 pt-0 border-t border-gray-100">
                <div className="mt-3 space-y-2">
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Company:</span> {email.company}
                  </div>
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Full timestamp:</span> {new Date(email.received_at).toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                    <p className="font-medium mb-1">Email Preview:</p>
                    <p className="text-gray-600 line-clamp-3">{email.body}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}