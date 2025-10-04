"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Chromium } from 'lucide-react'

export default function Home() {
  const [isLoading, setIsLoading] = useState(false)

  const handleGoogleSignIn = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      const data = await response.json()

      if (data.url) {

        window.location.href = data.url
      }
    } catch (error) {
      console.error('Error signing in:', error)
    } finally {
      setIsLoading(false)
    }
    }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-3xl font-bold tracking-tight">Welcome to <span className='text-amber-500'>Donna</span></CardTitle>
          <CardDescription className="text-base">Sign in to your account to continue</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            variant="outline"
            className="w-full h-12 text-base font-medium"
            onClick={handleGoogleSignIn}
            disabled={isLoading}
          >
            <Chromium className="mr-2 h-5 w-5" />
            {isLoading ? 'Signing in...' : 'Continue with Google'}
          </Button>
          
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Secure authentication</span>
            </div>
          </div>
          
          <p className="text-center text-xs text-muted-foreground px-4">By continuing, you agree to our Terms of Service and Privacy Policy</p>
        </CardContent>
      </Card>
    </div>
  )
}