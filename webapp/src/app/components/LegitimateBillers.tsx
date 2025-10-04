import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface Biller {
  id: number
  name: string
  domain: string
  logo: string
}

interface LegitimateBillersProps {
  billers: Biller[]
  itemsPerPage?: number
}

export default function LegitimateBillers({ billers, itemsPerPage = 4 }: LegitimateBillersProps) {
  const [carouselIndex, setCarouselIndex] = useState(0)
  const maxIndex = Math.max(0, billers.length - itemsPerPage)

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
                className="flex-1 min-w-0 p-4 bg-gray-50 border border-gray-200 rounded-lg hover:border-amber-500 transition-colors cursor-pointer"
              >
                <div className="flex flex-col items-center text-center space-y-2">
                  <div className="text-3xl">{biller.logo}</div>
                  <p className="font-semibold text-gray-900 text-sm">{biller.name}</p>
                  <p className="text-xs text-gray-500">{biller.domain}</p>
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
    </Card>
  )
}