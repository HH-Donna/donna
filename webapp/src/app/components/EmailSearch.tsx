import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, Filter } from 'lucide-react'

interface EmailSearchProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  onFilterClick?: () => void
}

export default function EmailSearch({ searchQuery, onSearchChange, onFilterClick }: EmailSearchProps) {
  return (
    <Card className="border-gray-200">
      <CardContent className="pt-6">
        <div className="flex items-center space-x-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search emails..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10 border-gray-300"
            />
          </div>
          <Button variant="outline" className="border-gray-300" onClick={onFilterClick}>
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}