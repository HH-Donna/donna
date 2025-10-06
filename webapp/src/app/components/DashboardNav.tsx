import { Button } from '@/components/ui/button'
import { Shield, LogOut } from 'lucide-react'
import { useState } from 'react'

interface DashboardNavProps {
  user: {
    name: string
    email: string
    companyName: string
    initials: string
    profileUrl?: string
  }
  onLogout?: () => void
}

export default function DashboardNav({ user, onLogout }: DashboardNavProps) {
  const [imageError, setImageError] = useState(false)
  
  console.log('👤 User profile data:', { 
    profileUrl: user.profileUrl, 
    hasProfileUrl: !!user.profileUrl,
    initials: user.initials 
  })
  
  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
      <div className="container mx-auto">
        <div className="flex items-center justify-between">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-sm">
              <span className="text-xl font-extrabold text-white">D</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Donna</h1>
              <p className="text-xs text-gray-500 -mt-1">Email Fraud Guard</p>
            </div>
          </div>
          
          {/* User Profile and Logout */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              {user.profileUrl && !imageError ? (
                <img 
                  src={user.profileUrl} 
                  alt={`${user.name} profile`} 
                  className="h-10 w-10 rounded-full border-2 border-gray-200 object-cover"
                  onError={() => {
                    console.log('❌ Failed to load profile image:', user.profileUrl)
                    setImageError(true)
                  }}
                  onLoad={() => console.log('✅ Profile image loaded successfully')}
                />
              ) : (
                <div className="h-10 w-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center text-white font-semibold shadow-sm">
                  {user.initials}
                </div>
              )}
              <div className="hidden md:block">
                <p className="text-sm font-medium text-gray-900">
                  {user.name.split(' ')[0]} from {user.companyName}
                </p>
                <p className="text-xs text-gray-500">{user.email}</p>
              </div>
            </div>
            
            <Button 
              variant="outline" 
              size="sm" 
              className="cursor-pointer border-gray-300 text-gray-600 hover:text-gray-900 hover:bg-gray-50 hover:border-gray-400 transition-all duration-200"
              onClick={onLogout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>
      </div>
    </nav>
  )
}