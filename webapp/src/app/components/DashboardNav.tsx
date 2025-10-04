import { Button } from '@/components/ui/button'
import { Shield, LogOut } from 'lucide-react'

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
  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Shield className="h-8 w-8 text-amber-500" />
          <h1 className="text-2xl font-bold text-gray-900">Donna</h1>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            {user.profileUrl ? (
                <img width={40} height={40} src={user.profileUrl} alt="Profile" className="h-10 w-10 rounded-full" />
            ): (
                <div className="h-10 w-10 rounded-full bg-gray-900 flex items-center justify-center text-white font-semibold">
                {user.initials}
                </div>
            )}
            <div className="text-sm">
              <div className='flex items-center space-x-2'>
                <p className="font-medium text-gray-900">{user.name} from {user.companyName}</p>
              </div>
              <p className="text-gray-500">{user.email}</p>
            </div>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            className="text-gray-600 hover:text-gray-900"
            onClick={onLogout}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </div>
    </nav>
  )
}