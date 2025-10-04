import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock, Building2 } from 'lucide-react'

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
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'flagged':
        return 'bg-amber-500'
      case 'resolved':
        return 'bg-green-500'
      case 'pending':
        return 'bg-yellow-500'
      default:
        return 'bg-red-500'
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <Card className="border-gray-200">
      <CardHeader>
        <CardTitle className="text-gray-900">Billing Emails</CardTitle>
        <CardDescription className="text-gray-500">
          Billing-related emails from your inbox
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {emails.map((email) => (
            <div
              key={email.id}
              className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:border-amber-500 hover:shadow-sm transition-all cursor-pointer"
              onClick={() => onEmailClick?.(email)}
            >
              <div className="flex items-center space-x-4 flex-1">
                <div className="h-12 w-12 rounded-full bg-gray-100 flex items-center justify-center">
                  <Building2 className="h-6 w-6 text-gray-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <p className="font-semibold text-gray-900">{email.company}</p>
                    <Badge className={`${getStatusColor(email.status)} text-white text-xs border-0`}>
                      {email.status}
                    </Badge>
                  </div>
                  <p className="text-sm font-medium text-gray-700 truncate">{email.subject}</p>
                  <p className="text-xs text-gray-500">{email.sender}</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm text-gray-500 flex items-center">
                    <Clock className="h-3 w-3 mr-1" />
                    {formatDate(email.received_at)}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}