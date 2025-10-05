import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ChevronLeft, ChevronRight, Building2, X, Mail, Phone, CreditCard, Calendar, Hash, MapPin, Clock, FileText, DollarSign } from 'lucide-react'
import { getCompanyLogoSources, getLogoDisplayName } from '../utils/logoUtils'

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
  itemsPerPage?: number
}

function BillerDetailModal({ biller, isOpen, onClose }: { biller: Biller | null, isOpen: boolean, onClose: () => void }) {
  if (!isOpen || !biller) return null

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  }

  const getFrequencyColor = (frequency?: string) => {
    switch (frequency?.toLowerCase()) {
      case 'monthly': return 'bg-green-100 text-green-800'
      case 'yearly': return 'bg-blue-100 text-blue-800'
      case 'quarterly': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />
      
      {/* Modal */}
      <Card className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white shadow-2xl">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div className="flex items-center space-x-4">
            <DynamicLogo 
              domain={biller.domain} 
              name={biller.name}
              className="w-12 h-12"
            />
            <div>
              <CardTitle className="text-xl text-gray-900">{biller.name}</CardTitle>
              <CardDescription className="text-gray-500">{biller.domain}</CardDescription>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Billing Frequency */}
          {biller.frequency && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                <Calendar className="h-5 w-5 mr-2 text-amber-600" />
                Billing Information
              </h3>
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-600">Billing Frequency:</span>
                <Badge className={getFrequencyColor(biller.frequency)}>{biller.frequency}</Badge>
              </div>
            </div>
          )}

          {/* Contact Information */}
          {((biller.contact_emails && biller.contact_emails.length > 0) || biller.billing_address) && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                <Mail className="h-5 w-5 mr-2 text-amber-600" />
                Contact Information
              </h3>
              <div className="space-y-3">
                {biller.billing_address && (
                  <div className="flex items-start space-x-2">
                    <MapPin className="h-4 w-4 text-gray-500 mt-0.5" />
                    <div>
                      <span className="text-sm text-gray-600 block">Billing Address:</span>
                      <span className="text-sm text-gray-900">{biller.billing_address}</span>
                    </div>
                  </div>
                )}
                
                {biller.contact_emails && biller.contact_emails.length > 0 && (
                  <div className="flex items-start space-x-2">
                    <Mail className="h-4 w-4 text-gray-500 mt-0.5" />
                    <div>
                      <span className="text-sm text-gray-600 block">Contact Emails:</span>
                      <div className="flex flex-wrap gap-1">
                        {biller.contact_emails.map((email, index) => (
                          <a key={index} href={`mailto:${email}`} className="text-sm text-blue-600 hover:underline">
                            {email}
                          </a>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Billing Details */}
          {(biller.biller_billing_details || biller.user_billing_details) && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                <FileText className="h-5 w-5 mr-2 text-amber-600" />
                Billing Details
              </h3>
              <div className="space-y-3">
                {biller.biller_billing_details && (
                  <div>
                    <span className="text-sm text-gray-600 block mb-1">Biller Details:</span>
                    <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-lg">{biller.biller_billing_details}</p>
                  </div>
                )}
                
                {biller.user_billing_details && (
                  <div>
                    <span className="text-sm text-gray-600 block mb-1">Account Details:</span>
                    <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-lg">{biller.user_billing_details}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Timeline - Show updated_at (more recent) */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
              <Clock className="h-5 w-5 mr-2 text-amber-600" />
              Timeline
            </h3>
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-gray-500" />
              <span className="text-sm text-gray-600">Last Updated:</span>
              <span className="text-sm text-gray-900">{formatDate(biller.updated_at)}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
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

export default function LegitimateBillers({ billers, itemsPerPage = 4 }: LegitimateBillersProps) {
  const [carouselIndex, setCarouselIndex] = useState(0)
  const [selectedBiller, setSelectedBiller] = useState<Biller | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const maxIndex = Math.max(0, billers.length - itemsPerPage)

  const handleBillerClick = (biller: Biller) => {
    setSelectedBiller(biller)
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setSelectedBiller(null)
  }

  const nextSlide = () => {
    setCarouselIndex((prev) => Math.min(prev + 1, maxIndex))
  }

  const prevSlide = () => {
    setCarouselIndex((prev) => Math.max(prev - 1, 0))
  }

  return (
    <Card className="border-gray-200">
      <CardHeader>
        <CardTitle className="text-gray-900">Legitimate Billers</CardTitle>
        <CardDescription className="text-gray-500">Identified from your customer emails</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <div className="flex items-center space-x-4 overflow-hidden">
            {billers.slice(carouselIndex, carouselIndex + itemsPerPage).map((biller) => (
              <div
                key={biller.id}
                className="flex-1 min-w-0 p-4 bg-gray-50 border border-gray-200 rounded-lg hover:border-amber-500 hover:shadow-md transition-all cursor-pointer group"
                onClick={() => handleBillerClick(biller)}
              >
                <div className="flex flex-col items-center text-center space-y-2">
                  <DynamicLogo 
                    domain={biller.domain} 
                    name={biller.name}
                    className="w-12 h-12 group-hover:scale-105 transition-transform"
                  />
                  <p className="font-semibold text-gray-900 text-xs">{biller.name}</p>
                  <p className="text-sm text-gray-500">{biller.domain}</p>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <Badge variant="outline" className="text-xs">
                      View Details
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {billers.length > itemsPerPage && (
            <>
              <button
                onClick={prevSlide}
                disabled={carouselIndex === 0}
                className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 h-8 w-8 rounded-full bg-white border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-5 w-5 text-gray-600" />
              </button>
              <button
                onClick={nextSlide}
                disabled={carouselIndex >= maxIndex}
                className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 h-8 w-8 rounded-full bg-white border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-5 w-5 text-gray-600" />
              </button>
            </>
          )}
        </div>
      </CardContent>
      
      {/* Modal */}
      <BillerDetailModal 
        biller={selectedBiller}
        isOpen={isModalOpen}
        onClose={closeModal}
      />
    </Card>
  )
}