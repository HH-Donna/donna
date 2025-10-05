import { Input } from '@/components/ui/input'
import { Search } from 'lucide-react'

interface EmailSearchProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  onFilterClick?: () => void
}

export default function EmailSearch({ searchQuery, onSearchChange }: EmailSearchProps) {
  return (
    <div className="mx-6 mb-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-900" />
        <Input
          placeholder="Search emails by subject, sender, or company..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-10 bg-white border-gray-300 shadow-sm hover:shadow-md hover:border-gray-400 focus:border-amber-500 focus:ring-amber-500 transition-all duration-200 text-sm"
        />
      </div>
    </div>
  )
}