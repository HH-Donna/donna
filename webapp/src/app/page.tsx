"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Shield, Zap, Key, Chromium, Check } from 'lucide-react'

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
      // setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen grid md:grid-cols-2 bg-white dark:from-slate-950 dark:to-slate-900">
      {/* Left: Brand / Promise */}
      <section className="hidden md:flex flex-col justify-center px-16 py-12">
        <div className="max-w-lg">
          <div className="flex items-center gap-3 mb-12">
            <div className="relative h-12 w-12 grid place-items-center rounded-2xl bg-gradient-to-br from-amber-300 to-amber-500 text-neutral-950 shadow-lg">
              <span className="text-2xl font-extrabold">D</span>
            </div>
            <div>
              <div className="text-3xl font-bold tracking-tight">Donna</div>
              <div className="text-sm uppercase tracking-wider text-muted-foreground/80">Email Fraud Guard</div>
            </div>
          </div>
          
          <h1 className="text-6xl font-bold tracking-tight leading-[1.1]">
            Stop email fraud <span className="text-amber-500">before it starts</span>
          </h1>
          <p className="mt-8 text-xl text-muted-foreground/90 leading-relaxed">
            <strong>Donna</strong> sets up in <span className="font-semibold">2 seconds</span> and flags fake invoices, look‑alike domains, and wire‑change scams — right in your inbox.
          </p>
          <ul className="mt-10 space-y-4 text-[15px] text-muted-foreground/80">
            <li className="flex items-center gap-3">
              <div className="h-6 w-6 rounded-full bg-amber-500/10 grid place-items-center">
                <Check className="h-4 w-4 text-amber-500" />
              </div>
              Instant domain look‑alike alerts
            </li>
            <li className="flex items-center gap-3">
              <div className="h-6 w-6 rounded-full bg-amber-500/10 grid place-items-center">
                <Check className="h-4 w-4 text-amber-500" />
              </div>
              Invoice tamper & bank‑detail drift detection
            </li>
            <li className="flex items-center gap-3">
              <div className="h-6 w-6 rounded-full bg-amber-500/10 grid place-items-center">
                <Check className="h-4 w-4 text-amber-500" />
              </div>
              Zero‑friction setup • Privacy‑first
            </li>
          </ul>
          <div className="mt-12 flex items-center gap-6 text-sm text-muted-foreground/70">
            <span className="inline-flex items-center gap-2">
              <Zap className="h-4 w-4" /> 2‑second setup
            </span>
          </div>
        </div>
      </section>

      {/* Right: Login Card */}
      <section className="flex items-center justify-center p-4 bg-gray-50/50 dark:bg-transparent">
        <div className="w-full max-w-md">
          <Card className="shadow-xl bg-white dark:bg-gray-10 backdrop-blur-sm">
            <CardContent className="space-y-6 pt-8 px-8">
              <Button
                variant="outline"
                className="w-full h-12 text-base font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors"
                onClick={handleGoogleSignIn}
                disabled={isLoading}
              >
                <Chromium className="mr-2 h-5 w-5 cursor-pointer" />
                {isLoading ? 'Setting up your protection...' : 'Continue with Google'}
              </Button>
              
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase tracking-wider">
                  <span className="bg-background px-3 text-muted-foreground/60">Zero-friction setup</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground/70">
                <div className="flex items-center justify-center gap-1.5">
                  <Key className="h-4 w-4" />
                  <span>Privacy-first</span>
                </div>
                <div className="flex items-center justify-center gap-1.5">
                  <Zap className="h-4 w-4" />
                  <span>2-sec setup</span>
                </div>
              </div>

              <p className="text-center text-xs text-muted-foreground/60">
                By continuing, you agree to our <a href="#" className="underline hover:text-foreground transition-colors">Terms</a> and <a href="#" className="underline hover:text-foreground transition-colors">Privacy Policy</a>
              </p>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  )
}