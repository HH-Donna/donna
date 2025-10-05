import { useState, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { Building2, ChevronRight, Calendar, Mail, MapPin, Clock } from 'lucide-react'
import { getCompanyLogoSources, getLogoDisplayName } from '../utils/logoUtils'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface Biller {
  id: string
  name: string
  domain: string
  billing_address?: string
  created_at: string
  profile_picture_url?: string
  payment_method?: string
  biller_billing_details?: string
  frequency?: string
  total_invoices?: number
  source_email_ids?: string[]
  user_id: string
  updated_at: string
  user_billing_details?: string
  contact_emails?: string[]
  user_account_number?: string
  biller_phone_number?: string
}

interface LegitimateBillersProps {
  billers: Biller[]
}

function DynamicLogo({ domain, name, className = "w-8 h-8" }: { domain: string, name: string, className?: string }) {
  const [logoError, setLogoError] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [currentSourceIndex, setCurrentSourceIndex] = useState(0)

  const logoSources = getCompanyLogoSources(domain, name)

  // Reset states when domain/name changes
  useEffect(() => {
    setLogoError(false)
    setIsLoading(true)
    setCurrentSourceIndex(0)
  }, [domain, name])

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (isLoading) {
        setIsLoading(false)
      }
    }, 100) 

    return () => clearTimeout(timeout)
  }, [isLoading, currentSourceIndex])

  const handleImageError = () => {
    if (currentSourceIndex < logoSources.length - 1) {
      setCurrentSourceIndex(currentSourceIndex + 1)
    } else {
      setLogoError(true)
      setIsLoading(false)
    }
  }

  const handleImageLoad = () => {
    setIsLoading(false)
    setLogoError(false)
  }

  if (logoError) {
    const initials = getLogoDisplayName(name)
    return (
      <div className={`${className} bg-gradient-to-br from-amber-400 to-amber-600 rounded-lg flex items-center justify-center text-white font-bold shadow-sm`}>
        <span className="text-sm">{initials}</span>
      </div>
    )
  }

  return (
    <div className={`${className} bg-white rounded-lg flex items-center justify-center overflow-hidden shadow-sm border border-gray-200`}>
      {isLoading && (
        <div className="animate-pulse bg-gray-200 w-full h-full rounded-lg flex items-center justify-center">
          <Building2 className="w-4 h-4 text-gray-400" />
        </div>
      )}
      <img
        src={logoSources[currentSourceIndex]}
        alt={`${name} logo`}
        className={`${className} object-contain ${isLoading ? 'hidden' : 'block'} `}
        onError={handleImageError}
        onLoad={handleImageLoad}
      />
    </div>
  )
}

export default function LegitimateBillers({ billers }: LegitimateBillersProps) {
  const [selectedBiller, setSelectedBiller] = useState<Biller | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleBillerClick = (biller: Biller) => {
    setSelectedBiller(biller)
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    // Delay clearing selected biller to prevent content flash during close animation
    setTimeout(() => setSelectedBiller(null), 200)
  }

  const getFrequencyBadgeColor = (frequency?: string) => {
    switch (frequency?.toLowerCase()) {
      case 'monthly': return 'bg-green-100 text-green-800 border-green-300'
      case 'yearly': return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'quarterly': return 'bg-purple-100 text-purple-800 border-purple-300'
      default: return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
    
    if (diffInDays === 0) return 'Today'
    if (diffInDays === 1) return 'Yesterday'
    if (diffInDays < 7) return `${diffInDays} days ago`
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`
    if (diffInDays < 365) return `${Math.floor(diffInDays / 30)} months ago`
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <>
      <div className="space-y-4 mr-4">
        <h3 className="text-lg font-bold text-gray-900 tracking-tight mb-2">Legitimate Billers</h3>
        <p className="text-sm text-gray-600 -mt-2 mb-4">Identified from your emails</p>
        
        <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
          {billers.map((biller) => (
            <div
              key={biller.id}
              className="flex items-center justify-between p-3 bg-white border border-gray-300 rounded-lg hover:shadow-md hover:border-gray-400 transition-all cursor-pointer group"
              onClick={() => handleBillerClick(biller)}
            >
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <DynamicLogo 
                  domain={biller.domain} 
                  name={biller.name}
                  className="w-10 h-10 flex-shrink-0"
                />
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-sm text-gray-900 truncate">{biller.name}</p>
                  <p className="text-xs text-gray-600 truncate">{biller.domain}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {biller.frequency && (
                  <Badge 
                    variant="outline" 
                    className={`text-xs px-2 py-0.5 font-semibold ${getFrequencyBadgeColor(biller.frequency)}`}
                  >
                    {biller.frequency}
                  </Badge>
                )}
                <ChevronRight className="h-4 w-4 text-gray-600 group-hover:text-gray-800 transition-colors" />
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Modal using shadcn Dialog */}
      <Dialog open={isModalOpen} onOpenChange={closeModal}>
        <DialogContent className="sm:max-w-[500px]">
          {selectedBiller && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3 mb-2">
                  <DynamicLogo 
                    domain={selectedBiller.domain} 
                    name={selectedBiller.name}
                    className="w-12 h-12"
                  />
                  <div>
                    <DialogTitle>{selectedBiller.name}</DialogTitle>
                    <DialogDescription>{selectedBiller.domain}</DialogDescription>
                  </div>
                </div>
              </DialogHeader>
              
              <div className="mt-4 space-y-4">
                {/* Billing Frequency */}
                {selectedBiller.frequency && (
                  <div className="flex items-center justify-between py-2">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Calendar className="h-4 w-4" />
                      <span>Billing Frequency</span>
                    </div>
                    <Badge 
                      variant="outline" 
                      className={`${getFrequencyBadgeColor(selectedBiller.frequency)}`}
                    >
                      {selectedBiller.frequency}
                    </Badge>
                  </div>
                )}

                {/* Contact Email */}
                {selectedBiller.contact_emails && selectedBiller.contact_emails.length > 0 && (
                  <div className="flex items-center justify-between py-2">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Mail className="h-4 w-4" />
                      <span>Contact</span>
                    </div>
                    <a 
                      href={`mailto:${selectedBiller.contact_emails[0]}`} 
                      className="text-sm text-blue-600 hover:underline"
                    >
                      {selectedBiller.contact_emails[0]}
                    </a>
                  </div>
                )}

                {/* Billing Address */}
                {selectedBiller.billing_address && (
                  <div className="py-2">
                    <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                      <MapPin className="h-4 w-4" />
                      <span>Billing Address</span>
                    </div>
                    <p className="text-sm text-gray-900 ml-6">
                      {selectedBiller.billing_address}
                    </p>
                  </div>
                )}

                {/* Last Updated */}
                <div className="flex items-center justify-between py-2 border-t pt-4">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Clock className="h-4 w-4" />
                    <span>Last updated</span>
                  </div>
                  <span className="text-sm text-gray-900">
                    {formatDate(selectedBiller.updated_at)}
                  </span>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}